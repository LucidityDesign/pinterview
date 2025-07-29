from fastapi import APIRouter, HTTPException
from ..models import Question, Tag, QuestionPublic, QuestionVote
from ..db.database import SessionDep
from sqlmodel import func, select
from sqlalchemy.orm import selectinload


router = APIRouter(
    prefix="/questions",
    tags=["questions"],
)

@router.get("/{item_id}",  response_model=QuestionPublic)
def read_question(session: SessionDep, item_id: int):
    question = session.exec(
        select(Question)
        .where(Question.id == item_id)
        .options(selectinload(Question.tags))
    ).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    return question

@router.get("/")
def list_questions(session: SessionDep, skip: int = 0, limit: int = 5):
    questions = session.exec(select(Question).offset(skip).limit(limit)).all()
    return questions

@router.post("/")
def create_question(session: SessionDep, question: Question):
    session.add(question)
    session.commit()
    session.refresh(question)
    return question

@router.post("/{item_id}/tags/{tag_id}", status_code=201, response_model=QuestionPublic)
def add_tag_to_question(session: SessionDep, item_id: int, tag_id: int):
    question = session.exec(select(Question).where(Question.id == item_id).options(selectinload(Question.tags))).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    # Fetch the tag from the database by its id or unique attribute
    db_tag = session.get(Tag, tag_id)
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    if db_tag not in question.tags:
        question.tags.append(db_tag)
        session.add(question)
        session.commit()
        session.refresh(question)

    return question

@router.post("/{item_id}/vote/up", status_code=201, response_model=QuestionPublic)
def vote_question_up(session: SessionDep, item_id: int):

    question = vote_question(session, item_id, 1)

    return question

@router.post("/{item_id}/vote/down", status_code=201, response_model=QuestionPublic)
def vote_question_down(session: SessionDep, item_id: int):
    question = vote_question(session, item_id, -1)

    return question

def vote_question(session: SessionDep, item_id: int, vote_value: int):

    question = session.get(Question, item_id)

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    vote = QuestionVote(question_id=question.id, vote_value=vote_value)

    session.add(vote)
    session.commit()
    session.refresh(question)

    vote_sum = session.exec(
        select(func.sum(QuestionVote.vote_value))
        .where(QuestionVote.question_id == item_id)
    ).first() or 0

    questionPublic = QuestionPublic.from_question(question)
    questionPublic.vote_sum = vote_sum or 0

    return questionPublic

