from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.models.link_tables import QuestionTagVote
from app.models.tag import TagPublic
from app.models.user import User
from app.routers.authentication import get_optional_current_user, get_required_current_user
from app.utils.user_voted import Vote, user_voted
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
def add_question_form(request: Request, current_user: User = Depends(get_required_current_user)):
    return templates.TemplateResponse("questions/add.html", {"request": request, "current_user": current_user})

@router.get("/{item_id}",  response_class=HTMLResponse, name="question")
def read_question(session: SessionDep, request: Request, item_id: int, current_user: User | None = Depends(get_optional_current_user)):

    statement = (
        select(Question, func.sum(QuestionVote.vote_value).label("vote_sum"))
        .where(Question.id == item_id)
        .outerjoin(QuestionVote)
        .options(selectinload(Question.user), selectinload(Question.tags))
        .group_by(Question.id)
        .order_by(desc("vote_sum"))
        .limit(1)
    )
    result = session.exec(statement).first()

    question, vote_sum = result if result else (None, 0)

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    question_public = QuestionPublic.from_question(question, current_user)
    question_public.vote_sum = vote_sum if vote_sum is not None else 0

    return templates.TemplateResponse("questions/index.html", {
        "request": request,
        "question": question_public,
        "current_user": current_user
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
def create_question(session: SessionDep, text: Annotated[str, Form()], current_user: User = Depends(get_required_current_user)):
    question = Question(text=text, created_by=current_user.id)
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
def vote_question_up(session: SessionDep, request: Request, item_id: int, current_user: User = Depends(get_required_current_user)):

    question = vote_question(session, item_id, 1, current_user)

    return templates.TemplateResponse("questions/item.html", {
        "request": request,
        "question": question
    })

@router.post("/{item_id}/vote/down", status_code=201, response_model=QuestionPublic)
def vote_question_down(session: SessionDep, request: Request, item_id: int, current_user: User = Depends(get_required_current_user)):
    question = vote_question(session, item_id, -1, current_user)

    return templates.TemplateResponse("questions/item.html", {
        "request": request,
        "question": question
    })

def vote_question(session: SessionDep, item_id: int, vote_value: int, current_user: User = Depends(get_required_current_user)):

    question = session.get(Question, item_id)

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    if user_voted(current_user, question) is not Vote.NEUTRAL:
        # remove existing vote if it exists
        existing_vote = session.exec(
            select(QuestionVote)
            .where(QuestionVote.question_id == item_id, QuestionVote.user_id == current_user.id)
        ).first()
        if existing_vote:
            session.delete(existing_vote)
            session.commit()
            # Recalculate vote sum after deletion
            vote_sum = session.exec(
                select(func.sum(QuestionVote.vote_value))
                .where(QuestionVote.question_id == item_id)
            ).first() or 0
            questionPublic = QuestionPublic.from_question(question, current_user)
            questionPublic.vote_sum = vote_sum or 0
            return questionPublic

    vote = QuestionVote(question_id=question.id, vote_value=vote_value, user_id=current_user.id)

    session.add(vote)
    session.commit()
    session.refresh(question)

    vote_sum = session.exec(
        select(func.sum(QuestionVote.vote_value))
        .where(QuestionVote.question_id == item_id)
    ).first() or 0

    questionPublic = QuestionPublic.from_question(question, current_user)
    questionPublic.vote_sum = vote_sum or 0

    return questionPublic


# Question-tag specific voting endpoints
@router.post("/{question_id}/tag/{tag_id}/vote/up", response_class=HTMLResponse)
def vote_question_tag_up(
    session: SessionDep,
    request: Request,
    question_id: int,
    tag_id: int,
    current_user: User = Depends(get_required_current_user)
):
    question, tag = vote_question_tag(session, question_id, tag_id, 1, current_user)
    return templates.TemplateResponse("tags/item.html", {
        "request": request,
        "tag": tag,
        "question": question
    })

@router.post("/{question_id}/tag/{tag_id}/vote/down", response_class=HTMLResponse)
def vote_question_tag_down(
    session: SessionDep,
    request: Request,
    question_id: int,
    tag_id: int,
    current_user: User = Depends(get_required_current_user)
):
    question, tag = vote_question_tag(session, question_id, tag_id, -1, current_user)
    return templates.TemplateResponse("tags/item.html", {
        "request": request,
        "tag": tag,
        "question": question
    })

def vote_question_tag(
    session: SessionDep,
    question_id: int,
    tag_id: int,
    vote_value: int,
    current_user: User
):
    # Verify question and tag exist
    question = session.get(Question, question_id)
    tag = session.get(Tag, tag_id)
    tagPublic = TagPublic.from_tag(tag, question, current_user)

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    if user_voted(current_user, question, tag) is not Vote.NEUTRAL:
        # remove existing vote if it exists
        existing_vote = session.exec(
            select(QuestionTagVote)
            .where(
                QuestionTagVote.question_id == question_id,
                QuestionTagVote.tag_id == tag_id,
                QuestionTagVote.user_id == current_user.id
            )
        ).first()
        if existing_vote:
            session.delete(existing_vote)
            session.commit()
            # Recalculate vote sum after deletion
            vote_sum = session.exec(
                select(func.sum(QuestionTagVote.vote_value))
                .where(
                    QuestionTagVote.question_id == question_id,
                    QuestionTagVote.tag_id == tag_id
                )
            ).first() or 0
            tagPublic.vote_sum = vote_sum or 0
            tagPublic.voted = Vote.NEUTRAL
            return question, tagPublic

    # Create vote on this specific question-tag combination
    vote = QuestionTagVote(
        user_id=current_user.id,
        question_id=question_id,
        tag_id=tag_id,
        vote_value=vote_value
    )

    session.add(vote)
    session.commit()

    # Calculate vote sum for this specific question-tag combination
    vote_sum = session.exec(
        select(func.sum(QuestionTagVote.vote_value))
        .where(
            QuestionTagVote.question_id == question_id,
            QuestionTagVote.tag_id == tag_id
        )
    ).first() or 0

    tagPublic.voted = Vote(vote_value)
    tagPublic.vote_sum = vote_sum or 0

    return question, tagPublic

