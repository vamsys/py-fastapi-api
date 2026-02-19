import datetime
from typing import List, Optional

from pydantic import BaseModel

from ..schemas.users import User

class DBConfig(BaseModel):
    host: str
    port: int
    dbname: str
    user: str
    password: str
	 
class Post(BaseModel):
	id: Optional[int] = None
	title: str
	content: str
	owner_id: int
	published: bool = True
	date: Optional[datetime.datetime] = None
	


class Posts(BaseModel):
	posts: List[Post]

	class Config:
		orm_mode = True


class PostCreate(BaseModel):
	title: str
	content: str
	published: bool = True

	class Config:
		orm_mode = True


class PostUpdate(BaseModel):
	title: str
	content: str
	published: bool

class PostOut(Post):
	owner: User

	class Config:
		orm_mode = True

class PostOutWithVotes(BaseModel):
	Posts: PostOut
	votes: int

	class Config:
		orm_mode = True	