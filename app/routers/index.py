from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates

from app.models.vote import QuestionVote
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
def render_front_page(request: Request, session: SessionDep):
    # Get questions to display on homepage
    statement = (
        select(Question, func.sum(QuestionVote.vote_value).label("vote_sum"))
        .outerjoin(QuestionVote)
        .group_by(Question.id)
        .limit(5)
        .order_by(desc("vote_sum"))
    )
    results = session.exec(statement).all()
    response = []

    for q, vote_sum in results:
        question_public = QuestionPublic.from_question(q)
        question_public.vote_sum = vote_sum if vote_sum is not None else 0
        response.append(question_public)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "questions": response
    })
