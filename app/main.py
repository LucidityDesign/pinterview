from typing import Union

from fastapi import FastAPI

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .routers import questions, tags, index
from .db.database import create_db_and_tables
from .models import User, Question, Tag, QuestionPublic, TagPublic

import logging
logging.basicConfig()
logger = logging.getLogger('sqlalchemy.engine')
logger.setLevel(logging.DEBUG)

app = FastAPI()

app.include_router(questions.router)
app.include_router(tags.router)
app.include_router(index.router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
