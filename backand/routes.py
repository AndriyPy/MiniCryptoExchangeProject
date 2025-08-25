import bcrypt
from fastapi import HTTPException,APIRouter, Depends, Response
from backand.database.database import Session
from backand.database.models import User as UserDbModel
from backand.auth.token_jwt import create_jwt_token, get_current_user, TokenData
from backand.crypto.bybit import run_ws
from backand.py_models import User, UserLogin, Update_User


router = APIRouter()



@router.get("/index")
async def index():
    ...


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
            )

            return {"message": f"user {new_user.name} has been created"}

    except Exception as e:
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
            )

            return {"message": "✅ Login successful",}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile", tags=["Profile"])
async def get_profile(current_user: TokenData = Depends(get_current_user)):
    return {
        "id": current_user.user_id,
        "email": current_user.email
    }


@router.post("/logout", tags=["Profile"])
async def logout(response: Response):
    response.delete_cookie(key="access_token")
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


