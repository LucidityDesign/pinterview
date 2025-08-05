from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
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
    questions: List["QuestionPublic"] = []

    # For displaying in templates - vote sum for a specific question context
    vote_sum: int = 0

    @classmethod
    def from_tag(cls, tag: Tag, question_id: Optional[int] = None):
        """
        Create TagPublic from Tag, optionally with vote sum for a specific question.
        If question_id is provided, vote_sum will be for that question-tag combination.
        """
        vote_sum = 0
        if question_id:
            # Calculate vote sum for this specific question-tag combination
            vote_sum = sum(
                vote.vote_value
                for vote in tag.question_tag_votes
                if vote.question_id == question_id
            )

        return cls(
            id=tag.id,
            name=tag.name,
            questions=tag.questions,
            vote_sum=vote_sum
        )

    class Config:
        from_attributes = True
