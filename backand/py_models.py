from pydantic import BaseModel, EmailStr, SecretStr, Field
from typing import Optional

class User(BaseModel):
    name: str = Field()
    email: EmailStr = Field(
        description="User email",
        examples=["john@gmail.com"])
    password: SecretStr = Field(
        description="User's password. Minimum 6 characters.",
        min_length=6
    )

class UserLogin(BaseModel):
    email: EmailStr = Field(
        description="User email",
        examples=["john@gmail.com"])
    password: SecretStr

class Update_User(BaseModel):
    name: Optional[str] = Field(
        None,
        description="New name"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="New email",
        examples=["john@gmail.com"]
    )
    password: Optional[SecretStr] = Field(
        None,
        description="New user's password. Minimum 6 characters.",
        min_length=6
    )
    password2: Optional[SecretStr] = Field(
        None,
        description="Confirm password"
    )
