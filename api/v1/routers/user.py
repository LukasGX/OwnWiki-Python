from fastapi import APIRouter, Depends, Form, Request
from api.v1.deps import connect_db
from services.user_service import login_s, logout_s

router = APIRouter()

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), redirect: str = Form(...), conn = Depends(connect_db)):
    return login_s(request, username, password, redirect, conn)

@router.post("/logout")
async def logout(request: Request):
    return logout_s(request)