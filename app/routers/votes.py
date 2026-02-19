from fastapi import APIRouter, Depends
from sqlmodel import select

from .. import models, schemas, utils
from ..models.db_orm import SessionDep

router = APIRouter(prefix="/votes", tags=["votes"])

@router.post("/", status_code=201, response_model=schemas.VoteResponse)
async def create_vote(
    vote: schemas.VoteCreate, 
    current_user: schemas.User = Depends(utils.get_current_user), 
    session: SessionDep = None
) -> schemas.VoteResponse:
    """Create a new vote entry."""
    vote_dict = vote.dict()
    vote_dict["user_id"] = current_user.id
    
    # Check if user has already voted for this post
    existing_vote = session.exec(
        select(models.Votes).where(
            (models.Votes.post_id == vote.post_id) & 
            (models.Votes.user_id == current_user.id)
        )
    ).first()
    
    if vote.direction == 1:
        if existing_vote:
            raise utils.AppException(status_code=409, detail="User has already voted on this post")
        new_vote = models.votes.create_vote_in_db_by_model(vote_dict, session)
        if new_vote:
            print("Vote created successfully")
            return new_vote
        raise utils.AppException(status_code=404, detail="Vote not created")
    else:  # direction == 0
        if not existing_vote:
            raise utils.AppException(status_code=404, detail="No vote found to remove")
        vote_dict.pop("direction", None)
        deleted_vote = models.votes.delete_vote_in_db_by_model(vote_dict, session)
        return deleted_vote
    