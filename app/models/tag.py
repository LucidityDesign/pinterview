from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from .link_tables import QuestionTagLink
# from .vote import TagVote

class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    questions: List["Question"] = Relationship(back_populates="tags", link_model=QuestionTagLink)
    votes: List["TagVote"] = Relationship(back_populates="tag")

class TagPublic(SQLModel):
    id: int
    name: str
    questions: List["QuestionPublic"] = []
    votes: List["TagVote"] = []

    vote_sum: int = 0

    @classmethod
    def from_tag(cls, tag: Tag):
        vote_sum = sum(vote.vote_value for vote in tag.votes)
        return cls(
            id=tag.id,
            name=tag.name,
            questions=tag.questions,
            votes=tag.votes,
            vote_sum=vote_sum
        )

    class Config:
        from_attributes = True
