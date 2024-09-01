from fastapi import APIRouter, Depends, HTTPException,Request
from auth.models import UserRegistration, UserConfirmation, Token
from auth.utils import create_access_token,cognito_client
from fastapi.security import OAuth2PasswordRequestForm
from botocore.exceptions import ClientError

auth_router = APIRouter()

def get_client_index(request:Request):
    return request.app.state.CLIENT_ID

@auth_router.post("/register/")
async def register_user(user: UserRegistration,client_id=Depends(get_client_index)):
    try:
        response = cognito_client.sign_up(
            ClientId=client_id,
            Username=user.name,
            Password=user.password,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': user.email
                },
            ],
        )
        return {"message": "User registered successfully", "user_sub": response['UserSub']}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response['Error']['Message'])
    

@auth_router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(),client_id=Depends(get_client_index)):
    try:
        response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': form_data.username,
                'PASSWORD': form_data.password,
            }
        )
        access_token = response['AuthenticationResult']['AccessToken']
        token_data = {"sub": form_data.username}
        jwt_token = create_access_token(token_data)
        return {"access_token": jwt_token, "token_type": "bearer"}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=f"Incorrect username or password {e}")
    

@auth_router.post("/confirm/")
async def confirm_user(user: UserConfirmation,client_id=Depends(get_client_index)):
    try:
        response = cognito_client.confirm_sign_up(
            ClientId=client_id,
            Username=user.email,
            ConfirmationCode=user.confirmation_code,
        )
        return {"message": "User confirmed successfully"}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response['Error']['Message'])
