from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

from .vote import QuestionVote, TagVote

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    hashed_password: str

    question_votes: List["QuestionVote"] = Relationship(back_populates="user")
    tag_votes: List["TagVote"] = Relationship(back_populates="user")
