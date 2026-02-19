import json
from datetime import datetime, timedelta
from typing import Optional
import paseto
from paseto.keys.symmetric_key import SymmetricKey
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from ..config import settings
from ..models.db_orm import get_session
from ..models import get_user_by_username_db
from ..models.users import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# Get or generate a secret key for token encryption
def get_secret_key() -> SymmetricKey:
    """Get the secret key from settings."""
    key_bytes = bytes.fromhex(settings.paseto_secret_key)
    return SymmetricKey.v4(key_bytes)


def create_paseto_token(
    username: str,
    expires_in_minutes: int = None
) -> str:
    """
    Create a PASETO token with user information.
    
    Args:
        username: The username
        expires_in_minutes: Token expiration time in minutes (default: from settings)
        
    Returns:
        The encrypted PASETO token as a string
    """
    if expires_in_minutes is None:
        expires_in_minutes = settings.access_token_expire_minutes
    
    secret_key = get_secret_key()
    
    # Create token payload
    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=expires_in_minutes)
    
    token_data = {
        "username": username,
        "iat": now.isoformat(),
        "exp": expires_at.isoformat(),
    }
    
    # Create and encrypt the token using PASETO v4 local (symmetric encryption)
    encrypted_token = paseto.create(
        key=secret_key,
        claims=token_data,
        purpose="local",
        exp_seconds=expires_in_minutes * 60
    )    
    return encrypted_token


def verify_paseto_token(token: str) -> dict:
    """
    Verify and decode a PASETO token.
    
    Args:
        token: The PASETO token string to verify
        
    Returns:
        Dictionary containing the token claims
        
    Raises:
        ValueError: If token is invalid or expired
    """
    secret_key = get_secret_key()
    
    try:
        # Verify and parse the token
        claims = paseto.parse(
            key=secret_key,
            token=token,
            purpose="local"
        )
        
        return claims
    except Exception as e:
        raise ValueError(f"Invalid token: {str(e)}")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    """
    Get the current authenticated user from the token.
    
    Args:
        token: The PASETO token from the Authorization header
        session: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify and decode the token
        claims = verify_paseto_token(token)
        username: str = claims["message"].get("username")
        print
        if username is None:
            raise credentials_exception            
    except ValueError:
        raise credentials_exception
    # Fetch user from database
    user = get_user_by_username_db(username, session)
   
    if user is None:
        raise credentials_exception
    
    return user
