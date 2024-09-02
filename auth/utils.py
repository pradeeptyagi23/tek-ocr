import boto3
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Any

# Initialize OAuth2PasswordBearer and Cognito client
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
cognito_client = boto3.client("cognito-idp", region_name="us-east-1")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> Any:
    """
    Verify if a plain password matches a hashed password.

    Args:
        plain_password (str): The plain text password.
        hashed_password (str): The hashed password.

    Returns:
        bool: True if the passwords match, otherwise False.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> Any:
    """
    Hash a password.

    Args:
        password (str): The plain text password.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def create_access_token(
    data: dict, expires_delta: timedelta = timedelta(minutes=15)
) -> Any:
    """
    Create an access token with an expiration time.

    Args:
        data (dict): The data to encode in the token.
        expires_delta (timedelta): The token expiration time (default is 15 minutes).

    Returns:
        str: The encoded JWT token.
    """
    encode_data = data.copy()
    expire = datetime.utcnow() + expires_delta
    encode_data.update({"exp": expire})
    encoded_jwt = jwt.encode(encode_data, "your-secret-key", algorithm="HS256")
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    Extract and validate the current user from the provided token.

    Args:
        token (str): The JWT token from the Authorization header.

    Returns:
        str: The username extracted from the token.

    Raises:
        HTTPException: If the token is invalid or the
        credentials could not be validated.
    """
    try:
        payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
