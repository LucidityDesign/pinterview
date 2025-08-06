from typing import TYPE_CHECKING
from enum import Enum

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from app.models.question import Question
    from app.models.tag import Tag
    from app.models.user import User

class Vote(Enum):
    DOWNVOTE = -1
    NEUTRAL = 0
    UPVOTE = 1

def user_voted(current_user: "User | None", question: "Question", tag: "Tag | None" = None) -> Vote:
    if not current_user:
        return Vote.NEUTRAL
    if tag:
        for vote in tag.question_tag_votes:
            if vote.user_id == current_user.id and vote.question_id == question.id:
                return Vote(vote.vote_value)
    elif question:
        for vote in question.votes:
            if vote.user_id == current_user.id:
                return Vote(vote.vote_value)

    return Vote.NEUTRAL
