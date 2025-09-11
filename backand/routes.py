import os
import datetime
from typing import Annotated
import bcrypt
import jwt
from fastapi import (
    HTTPException,
    APIRouter,
    Depends,
    Response,
    Query,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    Body)
from backand.database.database import Session
from backand.database.models import User as UserDbModel, Crypto
from backand.auth.token_jwt import create_jwt_token, get_current_user, TokenData, decode_jwt
from backand.py_models import User, UserLogin, Update_User
from fastapi.responses import RedirectResponse
import websockets
import json
import ssl, certifi
from backand.auth.google_auth import generate_google_oauth_redirect_uri
import aiohttp
from backand.auth.config import settings
import logging
from backand.bbb import fetch_klines, fetch_last_month_klines, save_klines
from backand.send_email import send_email


router = APIRouter()


logger = logging.getLogger("myapp")
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    file_handler = logging.FileHandler("py_log.log", mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

logger.propagate = False



BYBIT_URL = "https://api.bybit.com/v5/market/kline"
BYBIT_WS = "wss://stream.bybit.com/v5/public/spot"

ssl_context = ssl.create_default_context(cafile=certifi.where())


@router.get("/index")
async def index():
    try:
        with Session() as session:
            symbols = session.query(Crypto.symbol).distinct().all()
            return [{"symbol": s[0]} for s in symbols]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register", tags=["auth"])
async def register_user(user:User, response: Response):
    try:
        with Session() as session:
            existing_user = session.query(UserDbModel).filter(UserDbModel.email==user.email).first()

            if existing_user:
                raise HTTPException(status_code=400, detail="This email already registered")

            hashed_password = bcrypt.hashpw(user.password.get_secret_value().encode(), bcrypt.gensalt()).decode()

            new_user = UserDbModel(
                name = user.name,
                email = user.email,
                password = hashed_password
            )

            session.add(new_user)
            session.commit()

            jwt_token = create_jwt_token({"sub":new_user.email, "user_id":new_user.id})

            response.set_cookie(
                key="access_token",
                value=jwt_token,
                max_age=1800,
                secure=False,
                httponly=True,
                samesite="lax"
            )

            logger.info(f"✅ User created successfully: {new_user.email}")
            return {"message": f"user {new_user.name} has been created"}


    except Exception as e:
        logger.error(f"❌ Register error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/login", tags=["auth"])
def login(user: UserLogin, response: Response):
    try:
        with Session() as session:
            existing_user = session.query(UserDbModel).filter(UserDbModel.email == user.email).first()

            if not existing_user:
                raise HTTPException(status_code=400, detail="such user does not exist")

            if not bcrypt.checkpw(user.password.get_secret_value().encode(),existing_user.password.encode()):
                raise HTTPException(status_code=400, detail="Wrong password")

            jwt_token = create_jwt_token({"sub": existing_user.email, "user_id": existing_user.id, "scopes": ["user"]})

            response.set_cookie(
                key="access_token",
                value=jwt_token,
                max_age=1800,
                secure=False,
                httponly=True,
                samesite="lax"
            )

            logger.info(f"✅ User login successfully: {user.email}")
            return {"message": "✅ Login successful",}

    except Exception as e:
        logger.error(f"❌Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile", tags=["Profile"])
async def get_profile(current_user: TokenData = Depends(get_current_user)):
    with Session() as session:
        user = session.query(UserDbModel).filter_by(id=current_user.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
            "verified_email":user.verified_email,
        }


@router.post("/logout", tags=["Profile"])
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    logger.info("logout successful")
    return {"message": "✅ Logout successful"}


@router.delete("/delete_profile", tags=["Profile"])
async def delete_profile(response: Response,current_user: TokenData = Depends(get_current_user)):
    try:
        with Session() as session:
            existing_user = session.query(UserDbModel).filter(UserDbModel.email == current_user.email).first()

            if not existing_user:
                raise HTTPException(status_code=401, detail="you are not authorized")


            session.delete(existing_user)
            session.commit()

        response.delete_cookie(key="access_token")


        return {"message": "user was deleted"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.put("/update_profile", tags=["Profile"])
async def update_profile(response: Response, user:Update_User, current_user: TokenData = Depends(get_current_user)):
    try:
        with Session() as session:
            existing_user = session.query(UserDbModel).filter(UserDbModel.email == current_user.email).first()


            if not existing_user:
                raise HTTPException(status_code=401, detail="you are not authorized")

            if user.name:
                existing_user.name = user.name

            if user.email:
                email_in_use = session.query(UserDbModel).filter(UserDbModel.email == user.email,UserDbModel.id != existing_user.id).first()

                if email_in_use:
                    raise HTTPException(status_code=400, detail="user with this email exist")

            existing_user.email = user.email

            if user.password:
                if user.password != user.password2:
                    return {"message":"passwords do not match"}

                hashed_password = bcrypt.hashpw(user.password.get_secret_value().encode(), bcrypt.gensalt()).decode()

                existing_user.password = hashed_password

            session.commit()
            session.refresh(existing_user)


            new_jwt = create_jwt_token(
                {"sub": existing_user.email,
                 "user_id": existing_user.id,
                 "scopes": ["user"]}
            )

            response.set_cookie(
                key="access_token",
                value=new_jwt,
                max_age=1800,
                secure=False,
                httponly=True,
            )

            return {
                "message": "✅ Profile updated successfully",
                "user": {
                    "id": existing_user.id,
                    "name": existing_user.name,
                    "email": existing_user.email
                }
            }


    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/google/url", tags=["auth"])
def get_google_redirect_uri():
    uri = generate_google_oauth_redirect_uri()
    logger.info(f"🔗 Generated Google OAuth redirect URI: {uri}")
    return RedirectResponse(url=uri, status_code=302)

domain_name = os.getenv("DOMAIN_NAME")
@router.get("/google/callback", tags=["auth"])
async def handle_code(
        response: Response,
        code: str = Query(...),
):
    google_token_url = "https://oauth2.googleapis.com/token"
    logger.info(f"📥 Google callback triggered with code: {code}")

    print(code)

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=google_token_url,
            data={
                "client_id": settings.OAUTH_GOOGLE_CLIENT_ID,
                "client_secret": settings.OAUTH_GOOGLE_CLIENT_SECRET,
                "grant_type": "authorization_code",
                # "redirect_uri": "http://127.0.0.1:1489/google/callback",
                "redirect_uri": f"https://{domain_name}/google/callback",
                "code": code,
            },
            ssl=ssl_context
        ) as google_res:

            res = await google_res.json()

            id_token = res["id_token"]

            user_data = jwt.decode(
                id_token,
                algorithms=["RS256"],
                options={"verify_signature": False}
            )

    email = user_data["email"]
    name = user_data.get("name", "Google User")

    with Session() as session:
        user = session.query(UserDbModel).filter_by(email=email).first()
        if not user:
            new_user = UserDbModel(
                name=name,
                email=email,
                password=""
            )
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            logger.info(f"✅ New user created: {email}")
        else:
            new_user = user
            logger.info(f"✅ Existing user logged: {email}")

    new_jwt = create_jwt_token(
        {"sub": new_user.email,
         "user_id": new_user.id,
         "scopes": ["user"]}
    )

    response.set_cookie(
        key="access_token",
        value=new_jwt,
        max_age=1800,
        secure=False,
        httponly=True,
        samesite="lax",
    )

    response.status_code = 307
    # response.headers["Location"] = "http://127.0.0.1:5500/profile.html"
    response.headers["Location"] = f"https://{domain_name}/profile.html"

    return response


@router.get("/candles", tags=["Crypto"])
async def get_crypto(symbol:str= Query(...), current_user: TokenData = Depends(get_current_user)):
    try:
        with Session() as session:

            user = session.query(UserDbModel).filter_by(id=current_user.user_id).first()
            if not user:
                raise HTTPException(status_code=401, detail="You are not authorized")
            if not user.verified_email:
                raise HTTPException(status_code=401, detail="Email not verified")


            candles = (
                session.query(Crypto)
                .filter_by(symbol=symbol)
                .order_by(Crypto.timestamp.asc()) #asc фільтрує від старішої
                .all()
            )


            return [
                {
                    "timestamp": c.timestamp,
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume
                }
                for c in candles
            ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/wp-candles")
async def websocket_crypto(websocket: WebSocket, symbol: str, interval="1"):
    await websocket.accept()

    try:
        async with websockets.connect(BYBIT_WS, ssl=ssl_context) as bybit_ws:
            sub_msg = {
                "op": "subscribe",
                "args": [f"kline.{interval}.{symbol}"]
            }
            await bybit_ws.send(json.dumps(sub_msg))

            while True:
                msg = await bybit_ws.recv()
                data = json.loads(msg)

                print("📩 received from Bybit:", data)

                if "topic" in data and "kline" in data["topic"]:
                    kline = data["data"][0]
                    candle = {
                        "start": kline["start"],
                        "open": float(kline["open"]),
                        "high": float(kline["high"]),
                        "low": float(kline["low"]),
                        "close": float(kline["close"]),
                    }
                    await websocket.send_json(candle)
                    print()


    except WebSocketDisconnect:
        print("❌ Client disconected")

    except Exception as e:
        print("❌ error:", e)



@router.post("/verify_email", tags=["auth"])
async def verify_email(current_user: TokenData = Depends(get_current_user)):
    try:
        with Session() as session:
            user = session.query(UserDbModel).filter_by(id=current_user.user_id).first()

            if not user:
                raise HTTPException(status_code=404, detail="user not found")

            token = create_jwt_token(
                {"sub": user.email,
                 "user_id": user.id,
                 "scopes": ["verify_email"]},
                expires_delta=datetime.timedelta(minutes=5)
            )

            # link = f"http://127.0.0.1:1489/verify_email_confirm?token={token}"
            link = f"https://{domain_name}/verify_email_confirm?token={token}"

            send_email(user_name=user.name, user_email=user.email, link=link)

            return {"message":"посалання відправилося користувачу"}

    except Exception as e:
        print("❌ error:", e)


@router.get("/verify_email_confirm", tags=["auth"])
async def confirm_email(token: str = Query(...)):
    try:
        payload = decode_jwt(token)
        user_id = payload.get("user_id")

        with Session() as session:
            user = session.query(UserDbModel).filter_by(id=user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="user not found")

            user.verified_email = True
            logger.info(f"✅user: {user.email} confirmed email")
            session.commit()


        # return RedirectResponse("http://127.0.0.1:5500/profile.html")
        return RedirectResponse(f"https://{domain_name}/profile.html")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid token")



@router.post("/admin_add_crypto", tags=["Crypto"])
async def admin(symbol: str, interval: str = "60", current_user: TokenData = Depends(get_current_user)):
    try:
        with Session() as session:
            user = session.query(UserDbModel).filter_by(id=current_user.user_id).first()

            if not user:
                raise HTTPException(status_code=401, detail="you are not authorized")

            if not user.admin:
                raise HTTPException(status_code=403, detail="you are not admin")

            candles = fetch_last_month_klines(symbol=symbol, interval=interval)
            save_klines(candles, symbol=symbol, interval=interval)

            logger.info(f"✅ New {symbol} added successfully by {user.email}")
            return {"message":f"crypto {symbol} saved successfully"}

    except Exception as e:
        print("❌ error:", e)
