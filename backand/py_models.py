from pydantic import BaseModel, EmailStr, SecretStr, Field

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
    name: str = Field(
        None,
        description="New name")
    email: EmailStr = Field(
        None,
        description="New email",
        examples=["john@gmail.com"])
    password: SecretStr = Field(
        None,
        description="New user's password. Minimum 6 characters.",
        min_length=6
    )
    password2: SecretStr = Field(None, description="confirm password",)
