from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ..models import Question, Tag, QuestionPublic, QuestionVote
from ..db.database import SessionDep
from sqlmodel import desc, func, select
from sqlalchemy.orm import selectinload
from typing import Annotated

templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix="/questions",
    tags=["questions"],
)

@router.get("/add" , response_class=HTMLResponse)
def add_question_form(request: Request):
    return templates.TemplateResponse("questions/add.html", {"request": request})

@router.get("/{item_id}",  response_class=HTMLResponse, name="question")
def read_question(session: SessionDep, request: Request, item_id: int):
    question = session.exec(
        select(Question)
        .where(Question.id == item_id)
        .options(selectinload(Question.tags))
    ).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    return templates.TemplateResponse("questions/index.html", {
        "request": request,
        "question": question
    })

@router.get("/")
def list_questions(session: SessionDep,request: Request, skip: int = 0, limit: int = 5):
    statement = (
        select(Question, func.sum(QuestionVote.vote_value).label("vote_sum"))
        .outerjoin(QuestionVote)
        .group_by(Question.id)
        .offset(skip)
        .limit(limit)
        .order_by(desc("vote_sum"))
    )
    results = session.exec(statement).all()
    response = [QuestionPublic] * len(results)

    for i, (q, vote_sum) in enumerate(results):
        response[i] = QuestionPublic.from_question(q)
        response[i].vote_sum = vote_sum if vote_sum is not None else 0

    return templates.TemplateResponse("questions/list.html", {"questions": response, "request": request})

@router.post("/", response_class=RedirectResponse)
def create_question(session: SessionDep, text: Annotated[str, Form()]):
    question = Question(text=text)
    session.add(question)
    session.commit()
    session.refresh(question)
    # redirect to the newly created question
    return RedirectResponse(url=f"/questions/{question.id}", status_code=303)

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
def vote_question_up(session: SessionDep, request: Request, item_id: int):

    question = vote_question(session, item_id, 1)

    return templates.TemplateResponse("votes/item.html", {
        "request": request,
        "vote_sum": question.vote_sum
    })

@router.post("/{item_id}/vote/down", status_code=201, response_model=QuestionPublic)
def vote_question_down(session: SessionDep, request: Request, item_id: int):
    question = vote_question(session, item_id, -1)

    return templates.TemplateResponse("votes/item.html", {
        "request": request,
        "vote_sum": question.vote_sum
    })

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

