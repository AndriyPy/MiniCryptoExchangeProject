from dotenv import load_dotenv
import datetime
import os
from typing import Any
import secrets
import jwt
from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")


class TokenData(BaseModel):
    email: str
    user_id: int



def create_jwt_token(payload: dict[str, Any], expires_delta: datetime.timedelta | None=None):
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    payload_copy = payload.copy()

    if expires_delta is None:
        expires_delta = datetime.timedelta(minutes=30)

    expire = now_utc + (expires_delta if expires_delta else datetime.timedelta(minutes=30))
    jti = secrets.token_urlsafe()
    payload_copy.update({"exp": expire, "iat": now_utc, "jti": jti})

    try:
        token = jwt.encode(payload=payload_copy, key=SECRET_KEY, algorithm=ALGORITHM)
        return token
    except jwt.PyJWTError as e:
        raise ValueError(f"Error while encoding JWT: {e}") from e


def decode_jwt(encoded_token: str):
    try:
        token = jwt.decode(jwt=encoded_token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return token


def get_current_user(request: Request) -> TokenData:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_jwt(token)
    email = payload.get("sub")
    user_id = payload.get("user_id")

    if email is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    return TokenData(email=email, user_id=user_id)
