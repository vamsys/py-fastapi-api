from datetime import datetime
from typing import Annotated, Optional

from sqlalchemy import func, text
from sqlmodel import Field, Relationship, select

from ..models.users import User

from ..schemas.posts import Post, PostOutWithVotes
from .db_orm import BaseModel, SessionDep
from .votes import Votes


class Posts(BaseModel, table=True):
	__tablename__ = "posts"
	id: Annotated[int, Field(primary_key=True, index=True, nullable=False)]
	owner_id: Annotated[int, Field(nullable=False, foreign_key="user.id", ondelete="CASCADE")]
	title: Annotated[str, Field(nullable=False)]
	content: Annotated[str, Field(nullable=False)]
	published: bool = Field(default=True, nullable=False, sa_column_kwargs={"server_default": "true"})
	date: datetime = Field(default_factory=datetime.utcnow, nullable=False, sa_column_kwargs={"server_default": text("NOW()")})
	owner: Optional["User"] = Relationship()



def get_posts_from_db_by_model(session: SessionDep) -> list[Posts]:
	"""Fetch all posts from the database."""
	return session.exec(select(Posts)).all()


def get_posts_response(session: SessionDep) -> list[Post]:
	"""Fetch all posts and map them to the API response model."""
	db_posts = get_posts_from_db_by_model(session)
	return [
		Post(
			id=post.id,
			title=post.title,
			content=post.content,
			owner_id=post.owner_id,
			published=post.published,
			date=post.date,
		)
		for post in db_posts
	]


def get_post_from_db_by_model_by_id(post_id: int, session: SessionDep) -> Optional[Posts]:
	return session.exec(select(Posts).where(Posts.id == post_id)).first()


def create_post_in_db_by_model(post: dict, session: SessionDep) -> Optional[Posts]:
	new_post = Posts(**post)
	session.add(new_post)
	session.commit()
	session.refresh(new_post)
	return new_post


def delete_post_from_db_by_model(post_id: int, session: SessionDep) -> Optional[Posts]:
	post_to_delete = session.exec(select(Posts).where(Posts.id == post_id)).first()
	if post_to_delete:
		session.delete(post_to_delete)
		session.commit()
		return post_to_delete
	return None


def update_post_in_db_by_model(post_id: int, post: dict, session: SessionDep) -> Optional[Posts]:
	post_to_update = session.exec(select(Posts).where(Posts.id == post_id)).first()
	if post_to_update:
		post_to_update.title = post["title"]
		post_to_update.content = post["content"]
		post_to_update.published = post["published"]
		post_to_update.owner_id = post["owner_id"]
		session.add(post_to_update)
		session.commit()
		session.refresh(post_to_update)
		return post_to_update
	return None


def get_post_user_vote(post_id: int, session: SessionDep) -> Optional[PostOutWithVotes]:
	"""Return the vote of the current user for a specific post."""
	posts = session.exec(
		select(Posts, func.count(Votes.post_id).label("votes"))
		.outerjoin(Votes, Votes.post_id == Posts.id)
		.where(Posts.id == post_id)
		.group_by(Posts.id)
	).first()
	return posts