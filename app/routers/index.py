from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
from ..models import Question, Tag, QuestionPublic
from ..db.database import SessionDep
from sqlmodel import select
from sqlalchemy.orm import selectinload


router = APIRouter(
    tags=["index"],
)

templates = Jinja2Templates(directory="templates")

@router.get("/")
def render_front_page(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})
