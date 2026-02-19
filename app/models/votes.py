from datetime import datetime
from typing import Annotated, Optional

from sqlalchemy import text
from sqlmodel import Field, select

from .db_orm import BaseModel, SessionDep


class Votes(BaseModel, table=True):
    __tablename__ = "votes"
    post_id: Annotated[int, Field(nullable=False, foreign_key="posts.id", ondelete="CASCADE", primary_key=True)]
    user_id: Annotated[int, Field(nullable=False, foreign_key="user.id", ondelete="CASCADE", primary_key=True)]
    date: datetime = Field(default_factory=datetime.utcnow, nullable=False, sa_column_kwargs={"server_default": text("NOW()")})


def create_vote_in_db_by_model(vote: dict, session: SessionDep) -> Optional[Votes]:
    """Create a new vote in the database."""
    new_vote = Votes(**vote)
    session.add(new_vote)
    session.commit()
    session.refresh(new_vote)
    return new_vote


def delete_vote_in_db_by_model(vote: dict, session: SessionDep) -> Optional[Votes]:
    """Delete a vote from the database."""
    vote_tbd = session.exec(
        select(Votes).where(
            (Votes.post_id == vote["post_id"]) & (Votes.user_id == vote["user_id"])
        )
    ).first()
    if not vote_tbd:
        return None
    session.delete(vote_tbd)
    session.commit()
    return vote_tbd