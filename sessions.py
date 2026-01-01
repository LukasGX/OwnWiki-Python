from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from fastapi import Request
from typing import Any
from dotenv import load_dotenv
import os

class SessionData(BaseModel):
    username: str = ""

load_dotenv()

# get from .env
SECRET_KEY = os.getenv("session_secret_key")
if not SECRET_KEY:
    raise ValueError("session_secret_key is missing in .env file")

def init_middleware(app: Any) -> None:
    """Initialize session middleware on the given FastAPI/Starlette app.

    Usage: `init_middleware(app)` after creating the `FastAPI` instance.
    """
    app.add_middleware(
        SessionMiddleware,
        secret_key=SECRET_KEY,
        max_age=3600 * 24 * 7,  # 7 Tage
        https_only=True,
    )

# helper functions
def get_session_data(request: Request) -> Dict[str, Any]:
    return request.session

def set_session_data(request: Request, username: str):
    request.session["username"] = username

def clear_session(request: Request):
    request.session.clear()