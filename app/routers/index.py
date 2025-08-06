from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates

from app.models.user import User
from app.models.vote import QuestionVote
from app.routers.authentication import get_optional_current_user
from ..models import Question, Tag, QuestionPublic
from ..db.database import SessionDep
from sqlmodel import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, desc

router = APIRouter(
    tags=["index"],
)

templates = Jinja2Templates(directory="templates")

@router.get("/")
def render_front_page(request: Request, session: SessionDep, current_user: User | None = Depends(get_optional_current_user)):
    # Get questions to display on homepage
    statement = (
        select(Question, func.coalesce(func.sum(QuestionVote.vote_value), 0).label("vote_sum"))
        .outerjoin(QuestionVote)
        .group_by(Question.id)
        .limit(15)
        .order_by(desc("vote_sum"))
    )
    results = session.exec(statement).all()
    questions = []

    for q, vote_sum in results:
        question_public = QuestionPublic.from_question(q, current_user)
        question_public.vote_sum = vote_sum if vote_sum is not None else 0
        questions.append(question_public)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "questions": questions,
        "current_user": current_user
    })
