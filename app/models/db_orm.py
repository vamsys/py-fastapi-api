from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from ..config import settings

engine = create_engine(
    settings.database_url, 
    echo=settings.database_echo,
    pool_pre_ping=True  # Verify connections are alive before using them
)   

def create_db_and_tables():
    """Create all tables from SQLModel metadata."""
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(
        engine, 
        autocommit=False, 
        autoflush=True,
        expire_on_commit=False  # Keep objects attached after commit when working with existing tables
    ) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

class BaseModel(SQLModel):
    """Base model class with global table configuration"""
    __table_args__ = {"extend_existing": True}  # Use existing table if it already exists
    