from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

from app.models.tag import TagPublic
from app.models.user import User
from app.utils.user_voted import Vote, user_voted

from .link_tables import QuestionTagLink
from .vote import QuestionVote
# from .tag import Tag, TagPublic

class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    created_by: Optional[int] = Field(default=None, foreign_key="user.id")

    # Relationships
    user: Optional["User"] = Relationship(back_populates="questions")
    tags: List["Tag"] = Relationship(back_populates="questions", link_model=QuestionTagLink)
    votes: List["QuestionVote"] = Relationship(back_populates="question")
    tag_votes: List["QuestionTagVote"] = Relationship(back_populates="question")

class QuestionPublic(SQLModel):
    id: int
    text: str
    created_by: Optional[int] = None
    user: Optional["UserPublic"] = None
    tags: List["TagPublic"] = []
    votes: List["QuestionVote"] = []

    vote_sum: int = 0
    voted: Vote = Vote.NEUTRAL  # Indicates if the current user has voted on this question

    @classmethod
    def from_question(cls, question: Question, current_user: Optional[User] = None):
        # vote_sum = sum(vote.vote_value for vote in question.votes)
        tags_public = [TagPublic.from_tag(tag, question, current_user) for tag in question.tags]
        tags_public.sort(key=lambda t: t.vote_sum, reverse=True)

        voted = user_voted(current_user, question)

        return cls(
            id=question.id,
            text=question.text,
            created_by=question.created_by,
            user=question.user,
            tags=tags_public,
            voted=voted,
            # votes=question.votes,
            # vote_sum=vote_sum
        )

    class Config:
        from_attributes = True
