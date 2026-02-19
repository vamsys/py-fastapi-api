from typing import List

from fastapi import APIRouter, Depends, Response
from sqlalchemy import func
from sqlmodel import Session, select


from ..models.votes import Votes



from ..models.users import User
from ..utils.auth import get_current_user, get_session
from ..models.db_orm import SessionDep, get_session
from ..models.posts import *
from ..schemas.posts import *
from ..schemas.users import User as UserSchema
from ..utils.helpers import AppException
from ..models.posts import Posts

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("/", response_model=List[PostOutWithVotes])
async def get_posts(session: SessionDep, limit: int = 10, skip: int = 0, search: Optional[str] = "") -> List[PostOutWithVotes]:
	"""Retrieve list of all posts stored in posts table."""
	posts = session.exec(
		select(Posts, func.count(Votes.post_id).label("votes"))
		.outerjoin(Votes, Votes.post_id == Posts.id)
		.group_by(Posts.id)
		.filter(Posts.title.contains(search)).limit(limit).offset(skip)
	).all()
	return posts

@router.get("/{post_id}", response_model=PostOutWithVotes)
async def get_post(post_id: int, session: SessionDep):
	"""Fetch a single post by its integer ID."""
	post = get_post_user_vote(post_id, session)
	if post:
		return post
	raise AppException(status_code=404, detail="Post not found")


@router.post("/", status_code=201, response_model=PostCreate)
async def create_post(post: PostCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> PostCreate:
	"""Create a new post entry."""
	post_dict = {"owner_id": current_user.id, **post.dict()}
	new_post = create_post_in_db_by_model(post_dict, session)
	if new_post:
		return new_post
	raise AppException(status_code=404, detail="Post not found")


@router.delete("/{post_id}", status_code=204)
async def delete_post(post_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
	"""Remove a post by ID."""
	tbd_post = get_post_from_db_by_model_by_id(post_id, session)
	if not tbd_post:
		raise AppException(status_code=404, detail="Post not found")
	if tbd_post.owner_id != current_user.id:
		raise AppException(status_code=403, detail="Not authorized to delete this post")
	deleted_post = delete_post_from_db_by_model(post_id, session)
	if deleted_post:
		return Response(status_code=204)
	raise AppException(status_code=404, detail="Post not found")


@router.put("/{post_id}", response_model=PostCreate)
async def update_post(post_id: int, post: PostUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> Post:
	"""Update an existing post by ID."""
	print("Updating post with ID:", post_id)
	tbu_post = get_post_from_db_by_model_by_id(post_id, session)
	
	if not tbu_post:
		raise AppException(status_code=404, detail="Post not found")
	if tbu_post.owner_id != current_user.id:
		raise AppException(status_code=403, detail="Not authorized to update this post")
	post_dict = {"owner_id": current_user.id, **post.dict()}
	
	updated = update_post_in_db_by_model(post_id, post_dict, session)
	if updated:
		return updated
	raise AppException(status_code=404, detail="Post not found")
