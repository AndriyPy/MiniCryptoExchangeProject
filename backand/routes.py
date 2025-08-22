import bcrypt
from fastapi import FastAPI, HTTPException,APIRouter
from pydantic import BaseModel, EmailStr, SecretStr, Field
from backand.database.database import Session
from backand.database.models import User as UserDbModel
from backand.auth.ll import create_jwt_token, decode_jwt




router = APIRouter()


class User(BaseModel):
    name: str = Field()
    email: EmailStr = Field(description="User email", examples=["john@email.com"])
    password: SecretStr = Field(
        description="User's password. Minimum 6 characters.",
        min_length=6
    )



@router.post("/register")
async def register_user(user:User):
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

            return {f"user {new_user.name} has been created",
                    f"jwt_token = {jwt_token}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        session.close()




