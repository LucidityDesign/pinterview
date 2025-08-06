from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

from app.models.user import User
from app.utils.user_voted import Vote, user_voted
from .link_tables import QuestionTagLink
# from .vote import TagVote

class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    questions: List["Question"] = Relationship(back_populates="tags", link_model=QuestionTagLink)
    question_tag_votes: List["QuestionTagVote"] = Relationship(back_populates="tag")

class TagPublic(SQLModel):
    id: int
    name: str
    # questions: List["QuestionPublic"] = []

    # For displaying in templates - vote sum for a specific question context
    vote_sum: int = 0
    voted: Vote = Vote.NEUTRAL  # Indicates if the current user has voted on this tag

    @classmethod
    def from_tag(cls, tag: Tag, question: Optional["Question"] = None, current_user: Optional[User] = None):
        """
        Create TagPublic from Tag, optionally with vote sum for a specific question.
        If question is provided, vote_sum will be for that question-tag combination.
        """
        vote_sum = 0
        if question:
            # Calculate vote sum for this specific question-tag combination
            vote_sum = sum(
                vote.vote_value
                for vote in tag.question_tag_votes
                if vote.question_id == question.id
            )

        voted = user_voted(current_user, question, tag)

        return cls(
            id=tag.id,
            name=tag.name,
            # questions=tag.questions,
            vote_sum=vote_sum,
            voted=voted
        )

    class Config:
        from_attributes = True
