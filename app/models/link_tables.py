from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class QuestionTagLink(SQLModel, table=True):
    question_id: Optional[int] = Field(default=None, foreign_key="question.id", primary_key=True)
    tag_id: Optional[int] = Field(default=None, foreign_key="tag.id", primary_key=True)

class QuestionTagVote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable=False)
    question_id: int = Field(foreign_key="question.id")
    tag_id: int = Field(foreign_key="tag.id")
    vote_value: int  # 1 for upvote, -1 for downvote
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: "User" = Relationship(back_populates="question_tag_votes")
    question: "Question" = Relationship()
    tag: "Tag" = Relationship()
