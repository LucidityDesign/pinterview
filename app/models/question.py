from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

from .link_tables import QuestionTagLink
# from .vote import QuestionVote
# from .tag import Tag, TagPublic

class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    created_by: Optional[int] = Field(default=None, foreign_key="user.id")

    tags: List["Tag"] = Relationship(back_populates="questions", link_model=QuestionTagLink)
    votes: List["QuestionVote"] = Relationship(back_populates="question")

class QuestionPublic(SQLModel):
    id: int
    text: str
    created_by: Optional[int] = None
    tags: List["Tag"] = []
    votes: List["QuestionVote"] = []

    vote_sum: int = 0

    # @classmethod
    # def from_question(cls, question: Question):
    #     vote_sum = sum(vote.vote_value for vote in question.votes)
    #     return cls(
    #         id=question.id,
    #         text=question.text,
    #         created_by=question.created_by,
    #         tags=question.tags,
    #         votes=question.votes,
    #         vote_sum=vote_sum
    #     )

    @classmethod
    def from_question(cls, question: Question):
        vote_sum = sum(vote.vote_value for vote in question.votes)
        return cls(
            id=question.id,
            text=question.text,
            created_by=question.created_by,
            tags=question.tags,
            votes=question.votes,
            vote_sum=vote_sum
        )

    class Config:
        from_attributes = True
