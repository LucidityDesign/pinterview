from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class QuestionVote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable=False)
    question_id: int = Field(foreign_key="question.id")
    vote_value: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: "User" = Relationship(back_populates="question_votes")
    question: "Question" = Relationship(back_populates="votes")

# Remove TagVote since we're only using question-specific tag voting now
# class TagVote(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     user_id: int = Field(foreign_key="user.id", nullable=False)
#     tag_id: int = Field(foreign_key="tag.id")
#     vote_value: int
#     created_at: datetime = Field(default_factory=datetime.utcnow)

#     user: "User" = Relationship(back_populates="tag_votes")
#     tag: "Tag" = Relationship(back_populates="votes")
