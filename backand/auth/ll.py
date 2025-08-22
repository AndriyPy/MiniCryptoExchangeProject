from dotenv import load_dotenv
import datetime
import os
from typing import Any
import secrets
import jwt

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # fallback

def create_jwt_token(payload: dict[str, Any], expires_delta: datetime.timedelta | None = None):
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    payload_copy = payload.copy()

    expire = now_utc + (expires_delta if expires_delta else datetime.timedelta(minutes=30))
    jti = secrets.token_urlsafe()
    payload_copy.update({"exp": expire, "iat": now_utc, "jti": jti})

    try:
        token = jwt.encode(payload=payload_copy, key=SECRET_KEY, algorithm=ALGORITHM)
        return token
    except jwt.PyJWTError as e:
        raise ValueError(f"Error while encoding JWT: {e}") from e

    return token

def decode_jwt(encoded_token: bytes) -> dict[str, Any]:
    try:
        token = jwt.decode(jwt=encoded_token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError as e:
        raise ValueError(f"Error while decoding JWT: {e}") from e

    return token
