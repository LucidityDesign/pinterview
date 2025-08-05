from .user import User, UserPublic, UserCreate, UserUpdate
from .question import Question, QuestionPublic
from .tag import Tag, TagPublic
from .vote import QuestionVote, TagVote
from .link_tables import QuestionTagLink

from sqlmodel import SQLModel

# Resolve forward references after all imports
Question.model_rebuild()
QuestionPublic.model_rebuild()
Tag.model_rebuild()
TagPublic.model_rebuild()

__all__ = [
    "User",
    "Question",
    "QuestionPublic",
    "Tag",
    "TagPublic",
    "QuestionVote",
    "TagVote",
    "QuestionTagLink"
]
