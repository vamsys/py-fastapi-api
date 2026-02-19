from datetime import datetime
from typing import Annotated, Optional

from pydantic import EmailStr
from app.models.db_orm import SessionDep
from sqlmodel import Field, SQLModel, SQLModel, select, text
from argon2 import PasswordHasher   


# Create a PasswordHasher instance
ph = PasswordHasher()

class BaseModel(SQLModel):
    """Base model class with global table configuration"""
    __table_args__ = {"extend_existing": True}  # Use existing table if it already exists


class User(BaseModel, table=True):
    __tablename__ = "user"
    id: Annotated[int, Field(primary_key=True, index=True, nullable=False)]
    username: Annotated[str, Field(nullable=False, unique=True)]
    email: Annotated[EmailStr, Field(nullable=False, unique=True)]
    password_hash: Annotated[str, Field(nullable=False)]
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, sa_column_kwargs={"server_default": text("NOW()")})


def hash_password(password: str) -> str:
    """Hash a plain text password using Argon2"""
    return ph.hash(password)

def verify_password(hashed_password: str, plain_password: str) -> bool:
    """Verify a plain text password against the hashed version"""
    return ph.verify(hashed_password, plain_password)


def get_user_by_id(user_id: int, session: SessionDep) -> Optional[User]:
    """Fetch a user by ID from the database."""
    return session.exec(select(User).where(User.id == user_id)).first()


def get_user_by_username_db(username: str, session: SessionDep) -> Optional[User]:
    """Fetch a user by username from the database."""
    return session.exec(select(User).where(User.username == username)).first()

def get_user_by_email_db(email: str, session: SessionDep) -> Optional[User]:
    """Fetch a user by email from the database."""
    return session.exec(select(User).where(User.email == email)).first()


def create_new_user_db(user: dict, session: SessionDep) -> Optional[User]:
    """Create a new user in the database."""
    hashed_pwd = hash_password(user["password"])
    user["password_hash"] = hashed_pwd
    new_user = User(**user)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user
