from pydantic import BaseModel, EmailStr

class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserConfirmation(BaseModel):
    email: EmailStr
    confirmation_code: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
