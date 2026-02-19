from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..models.db_orm import SessionDep, get_session
from ..schemas.users import User
from ..utils.auth import get_current_user
from ..models import create_new_user_db, get_user_by_id, get_user_by_username_db
from ..schemas import users
from ..utils.helpers import AppException

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", status_code=201, response_model=users.UserCreateResponse)
async def create_user(user: users.UserCreate, session: Session = Depends(get_session)) -> users.UserCreateResponse:
	"""Create a new user entry."""
	user_dict = user.dict()
	new_user = create_new_user_db(user_dict, session)
	if new_user:
		return new_user
	raise AppException(status_code=404, detail="User not found")


@router.get("/{user_id}", response_model=users.User)
async def get_user(user_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> users.User:
	"""Fetch a single user by its integer ID."""
	user = get_user_by_id(user_id, session)
	if user:
		return user
	raise AppException(status_code=404, detail="User not found")


@router.get("/{username}", response_model=users.User)
async def get_user_by_username(username: str, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> users.User:
	"""Fetch a single user by its username."""
	user = get_user_by_username_db(username, session)
	if user:
		return user
	raise AppException(status_code=404, detail="User not found")
	    
	

