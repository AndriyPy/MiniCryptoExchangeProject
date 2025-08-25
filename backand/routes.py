import bcrypt
from fastapi import HTTPException,APIRouter, Depends, Request, Response
from pydantic import BaseModel, EmailStr, SecretStr, Field
from backand.database.database import Session
from backand.database.models import User as UserDbModel
from backand.auth.token_jwt import create_jwt_token, get_current_user, TokenData


router = APIRouter()

class User(BaseModel):
    name: str = Field()
    email: EmailStr = Field(description="User email", examples=["john@email.com"])
    password: SecretStr = Field(
        description="User's password. Minimum 6 characters.",
        min_length=6
    )

class UserLogin(BaseModel):
    email: EmailStr
    password: SecretStr

@router.post("/register")
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

    finally:
        session.close()


@router.post("/login")
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

    finally:
        session.close()


@router.get("/profile")
async def get_profile(current_user: TokenData = Depends(get_current_user)):
    return {
        "id": current_user.user_id,
        "email": current_user.email
    }

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "✅ Logout successful"}
