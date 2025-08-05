from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Form
from pydantic import BaseModel
from sqlmodel import or_, select

from app.db.database import SessionDep
from app.models.user import UserPublic
from ..models import User
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Request
from fastapi import Depends, FastAPI, HTTPException, status
import jwt
from jwt.exceptions import InvalidTokenError

from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from passlib.context import CryptContext

# Custom OAuth2 scheme that checks cookies instead of Authorization header
class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> str | None:
        # First try to get token from cookie
        token = request.cookies.get("access_token")
        if token:
            return token

        # Fall back to Authorization header for API endpoints
        return await super().__call__(request)

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "b05d8a3bb23dbe54ff0cb6b2fbfb7f6ce783d0fd7a12673c26a07365e44b12a2"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
templates = Jinja2Templates(directory="templates")

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="auth/token")

app = FastAPI()
router = APIRouter(
    tags=["auth"],
    prefix="/auth",
)
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(session: SessionDep, username: str | None = None, email: str | None = None):

    statement = select(User).where(or_(User.username == username, User.email == email))
    user = session.exec(statement).first()
    return user


def authenticate_user(session: SessionDep, username: str, email: str, password: str):
    user = get_user(session, username, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Handle case where no token is provided (optional authentication)
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(session, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    # if current_user.disabled:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.post("/token")
async def login_for_access_token(
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(session, form_data.username, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/register", response_class=HTMLResponse)
async def get_register_page(request: Request):
    return templates.TemplateResponse("users/register.html", {"request": request})

@router.post("/users/register", response_class=HTMLResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    session: SessionDep,
    request: Request,
    username: str = Form(min_length=3, max_length=50, description="Username must be between 3 and 50 characters"),
    password: str = Form(min_length=8, max_length=128, description="Password must be between 8 and 128 characters"),
    email: str = Form(min_length=5, max_length=128, description="Email must be between 5 and 128 characters"),
):
    form_data = await request.form()
    # Check if the user already exists
    existing_user = session.exec(select(User).where(or_(User.email == email, User.username == username))).first()

    if existing_user:
        return templates.TemplateResponse("users/register.html", {"request": request, "error": "User already exists!", "form_data": form_data}, status_code=status.HTTP_400_BAD_REQUEST)

    new_user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
    )


    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return templates.TemplateResponse("users/register.html", {"request": request, "success": "User registered successfully!", "form_data": form_data}, status_code=status.HTTP_201_CREATED)


@router.get("/users/login", response_class=HTMLResponse)
async def get_login_page(request: Request):
    form_data = await request.form()
    return templates.TemplateResponse("users/login.html", {"request": request, "form_data": form_data})

@router.post("/users/login", response_class=HTMLResponse)
async def login_user(
    session: SessionDep,
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    form_data = await request.form()
    user = authenticate_user(session, username, username, password=password)
    if not user:
        return templates.TemplateResponse("users/login.html", {"request": request, "error": "Invalid username or password", "form_data": form_data}, status_code=status.HTTP_401_UNAUTHORIZED)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    response = templates.TemplateResponse("users/login.html", {"request": request, "success": "Login successful!", "form_data": form_data}, status_code=status.HTTP_200_OK)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,          # Prevents JavaScript access (XSS protection)
        secure=True,            # Only send over HTTPS in production
        samesite="lax",         # CSRF protection
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Cookie expires with token
    )
    return response

@router.get("/users/me/", response_model=UserPublic)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@router.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]

@router.post("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    response = templates.TemplateResponse("users/login.html", {
        "request": request,
        "success": "Logged out successfully!"
    })
    response.delete_cookie(key="access_token")
    return response
