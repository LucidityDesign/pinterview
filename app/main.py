
from fastapi import FastAPI, HTTPException, Request

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates

from .routers import questions, tags, index, authentication
from .db.database import create_db_and_tables

import logging

logging.basicConfig()
logger = logging.getLogger('sqlalchemy.engine')
logger.setLevel(logging.DEBUG)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.include_router(questions.router)
app.include_router(tags.router)
app.include_router(index.router)
app.include_router(authentication.router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Extract data from the request (optional)
    form_data = await request.form()

    if request.url.path.startswith("/auth"):
        return templates.TemplateResponse(
            "users/register.html",
            {
                "request": request,
                "error": "Invalid input. Please check your data.",
                "details": exc.errors(),
                "form_data": form_data  # optional: pre-fill form values
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    return HTMLResponse("Invalid input", status_code=422)

@app.exception_handler(401)
async def unauthorized_exception_handler(request: Request, exc: HTTPException):
    # TODO: Check if a redirect is always the right solution
    # redirect to login page
    return RedirectResponse(url="/auth/users/login", status_code=status.HTTP_302_FOUND)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
