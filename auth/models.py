from pydantic import BaseModel, EmailStr


class UserRegistration(BaseModel):
    """
    Model for user registration data.

    Attributes:
        email (EmailStr): The email address of the user.
        password (str): The password for the user.
        name (str): The name of the user.
    """

    email: EmailStr
    password: str
    name: str


class UserConfirmation(BaseModel):
    """
    Model for user confirmation data.

    Attributes:
        email (EmailStr): The email address of the user.
        confirmation_code (str): The confirmation code sent to the user.
    """

    email: EmailStr
    confirmation_code: str


class Token(BaseModel):
    """
    Model for authentication tokens.

    Attributes:
        access_token (str): The JWT access token.
        token_type (str): The type of the token, default is "bearer".
    """

    access_token: str
    token_type: str = "bearer"
