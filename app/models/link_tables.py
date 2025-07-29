from typing import Optional
from sqlmodel import SQLModel, Field

class QuestionTagLink(SQLModel, table=True):
    question_id: Optional[int] = Field(default=None, foreign_key="question.id", primary_key=True)
    tag_id: Optional[int] = Field(default=None, foreign_key="tag.id", primary_key=True)
