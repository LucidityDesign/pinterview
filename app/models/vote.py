from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class QuestionVote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable=True)
    question_id: int = Field(foreign_key="question.id")
    vote_value: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: "User" = Relationship(back_populates="question_votes")
    question: "Question" = Relationship(back_populates="votes")


class TagVote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable=True)
    tag_id: int = Field(foreign_key="tag.id")
    vote_value: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: "User" = Relationship(back_populates="tag_votes")
    tag: "Tag" = Relationship(back_populates="votes")
