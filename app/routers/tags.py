from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.user import User
from app.routers.authentication import get_current_active_user
from ..models import Tag, TagPublic, Question, QuestionTagVote
from ..db.database import SessionDep
from sqlmodel import func, select
from sqlalchemy.orm import selectinload

templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix="/tags",
    tags=["tags"],
)

@router.get("/{item_id}", response_model=TagPublic)
def read_tag(session: SessionDep, item_id: int):
    tag = session.exec(select(Tag).where(Tag.id == item_id).options(selectinload(Tag.questions))).first()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    return tag

@router.get("/")
def list_tags(session: SessionDep, skip: int = 0, limit: int = 5):
    tags = session.exec(select(Tag).offset(skip).limit(limit)).all()
    return tags

@router.post("/")
def create_tag(session: SessionDep, request: Request, name: str = Form(...), question_id: int = Form(...), current_user: User = Depends(get_current_active_user)):
    # First, check if the question exists
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Check if tag with this name already exists
    existing_tag = session.exec(select(Tag).where(Tag.name == name)).first()

    if existing_tag:
        # Tag exists, just add it to the question if not already connected
        if existing_tag not in question.tags:
            question.tags.append(existing_tag)
            session.add(question)
            session.commit()
            session.refresh(existing_tag)
        return templates.TemplateResponse("tags/item.html", {
            "request": request,
            "tag": TagPublic.from_tag(existing_tag)
        })
    else:
        # Create new tag and connect it to the question
        tag = Tag(name=name)
        session.add(tag)
        session.flush()  # Flush to get the tag ID

        # Add the tag to the question
        question.tags.append(tag)
        session.add(question)
        session.commit()
        session.refresh(tag)

        return templates.TemplateResponse("tags/item.html", {
            "request": request,
            "tag": TagPublic.from_tag(tag)
        })

# Question-tag specific voting endpoints
@router.post("/question/{question_id}/tag/{tag_id}/vote/up", response_class=HTMLResponse)
def vote_question_tag_up(
    session: SessionDep,
    request: Request,
    question_id: int,
    tag_id: int,
    current_user: User = Depends(get_current_active_user)
):
    vote_sum = vote_question_tag(session, question_id, tag_id, 1, current_user)
    return templates.TemplateResponse("votes/item.html", {
        "request": request,
        "vote_sum": vote_sum
    })
def vote_question_tag_up(
    session: SessionDep,
    request: Request,
    question_id: int,
    tag_id: int,
    current_user: User = Depends(get_current_active_user)
):
    vote_sum = vote_question_tag(session, question_id, tag_id, 1, current_user)
    return templates.TemplateResponse("votes/item.html", {
        "request": request,
        "vote_sum": vote_sum
    })

@router.post("/question/{question_id}/tag/{tag_id}/vote/down", response_class=HTMLResponse)
def vote_question_tag_down(
    session: SessionDep,
    request: Request,
    question_id: int,
    tag_id: int,
    current_user: User = Depends(get_current_active_user)
):
    vote_sum = vote_question_tag(session, question_id, tag_id, -1, current_user)
    return templates.TemplateResponse("votes/item.html", {
        "request": request,
        "vote_sum": vote_sum
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

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

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

    return vote_sum
