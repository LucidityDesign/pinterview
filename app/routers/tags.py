from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ..models import Tag, TagPublic, TagVote
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
def create_tag(tag: Tag, session: SessionDep):
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.post("/{item_id}/vote/up", response_class=HTMLResponse)
def vote_tag_up(session: SessionDep, request: Request, item_id: int):

    tag = vote_tag(session, item_id, 1)

    return templates.TemplateResponse("votes/item.html", {
        "request": request,
        "vote_sum": tag.vote_sum
    })

@router.post("/{item_id}/vote/down", response_class=HTMLResponse)
def vote_tag_down(session: SessionDep, request: Request, item_id: int):
    tag = vote_tag(session, item_id, -1)

    return templates.TemplateResponse("votes/item.html", {
        "request": request,
        "vote_sum": tag.vote_sum
    })

def vote_tag(session: SessionDep, item_id: int, vote_value: int):

    tag = session.get(Tag, item_id)

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    vote = TagVote(tag_id=tag.id, vote_value=vote_value)

    session.add(vote)
    session.commit()
    session.refresh(tag)

    vote_sum = session.exec(
        select(func.sum(TagVote.vote_value))
        .where(TagVote.tag_id == item_id)
    ).first() or 0

    tagPublic = TagPublic.from_tag(tag)
    tagPublic.vote_sum = vote_sum or 0

    return tagPublic
