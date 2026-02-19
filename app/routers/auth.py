from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from .. import models, schemas, utils
from ..models.db_orm import SessionDep, get_session, Session
from ..models import *
from ..utils.auth import *
from ..schemas.users import LoginResponse


router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=LoginResponse)
async def login(user_credentials: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)): # type: ignore
    """Authenticate a user and return a PASETO token."""

    user = models.get_user_by_email_db(user_credentials.username, session)
    if not user:
        raise utils.AppException(status_code=401, detail="Invalid email or password")
    if not models.users.verify_password(user.password_hash, user_credentials.password):
        raise utils.AppException(status_code=401, detail="Invalid email or password")
    
    # Create PASETO token
    token = create_paseto_token(
        username=user.username,
        expires_in_minutes=60
    )
    
    return LoginResponse(
        access_token=token,
        token_type="Bearer",
        username=user.username
    )  