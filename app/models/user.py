from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

from .vote import QuestionVote, TagVote

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str

    # Relationships
    questions: List["Question"] = Relationship(back_populates="user")
    question_votes: List["QuestionVote"] = Relationship(back_populates="user")
    tag_votes: List["TagVote"] = Relationship(back_populates="user")

class UserPublic(SQLModel):
    id: int
    email: str
    username: str
    # Note: hashed_password is intentionally excluded for security

class UserCreate(SQLModel):
    email: str
    username: str
    password: str  # Plain password for input, will be hashed before storing

class UserUpdate(SQLModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None  # Will be hashed if provided
