from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, Field


class VoteCreate(BaseModel):
    post_id: int
    direction: Annotated[int, Field(ge=0, le=1)]

    class Config:
        orm_mode = True


class VoteResponse(BaseModel):
    post_id: int
    user_id: int
    date: Optional[datetime] = None
    
    class Config:
        orm_mode = True
