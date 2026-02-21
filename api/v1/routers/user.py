from fastapi import APIRouter, Depends, Form, Request
from pydantic import BaseModel
from api.v1.deps import connect_db
from services.user_service import get_encrypted, login_s, logout_s, get_roles_s, change_roles_s
from api.v1.deps import protect, protect_with_rights
from typing import Dict, List

router = APIRouter()

protect_read = protect_with_rights(["read"])
protect_debug = protect_with_rights(["debug"])
protect_userrights = protect_with_rights(["userrights"])

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

class RoleUpdate(BaseModel):
    roles: Dict[str, bool]

@router.patch("/{username}/roles")
async def change_roles(
    username: str, 
    role_data: RoleUpdate,
    user_roles: Dict[str, List[str]] = Depends(protect_userrights)
):
    """Required right: userrights"""
    roles_dict = role_data.roles
    return change_roles_s(username, roles_dict)