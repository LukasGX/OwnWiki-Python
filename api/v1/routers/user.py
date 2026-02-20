from fastapi import APIRouter, Depends, Form, Request
from api.v1.deps import connect_db
from services.user_service import get_encrypted, login_s, logout_s, get_roles_s
from api.v1.deps import protect, protect_with_rights
from typing import Dict, List

router = APIRouter()

protect_read = protect_with_rights(["read"])
protect_debug = protect_with_rights(["debug"])

@router.post("/encrypt")
async def encrypt(request: Request, input: str, user_roles: Dict[str, List[str]] = Depends(protect_debug)):
    """Required right: debug"""
    return {"hash": get_encrypted(input)}

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), redirect: str = Form(...), conn = Depends(connect_db)):
    return login_s(request, username, password, redirect, conn)

@router.post("/logout")
async def logout(request: Request):
    return logout_s(request)

@router.get("/{username}/roles")
async def get_roles(request: Request, username: str, user_roles: Dict[str, List[str]] = Depends(protect_read)):
    """Required right: read"""
    return get_roles_s(username)