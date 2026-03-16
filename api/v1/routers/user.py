from fastapi import APIRouter, Depends, Form, Request, Body
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from api.v1.deps import connect_db
from services.user_service import get_encrypted, login_s, logout_s, get_roles_s, change_roles_s, register_s, activate_account_s, rename_s, block_user_s, send_email_s, get_block_info_s
from api.v1.deps import protect, protect_with_rights
from typing import Dict, List

router = APIRouter()

protect_read = protect_with_rights(["read"])
protect_debug = protect_with_rights(["debug"])
protect_userrights = protect_with_rights(["userrights"])
protect_block = protect_with_rights(["block"])
protect_renameusers = protect_with_rights(["renameusers"])

@router.post("/encrypt")
async def encrypt(request: Request, input: str, user_roles: Dict[str, List[str]] = Depends(protect_debug)):
    """Required right: debug"""
    return {"hash": get_encrypted(input)}

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), redirect: str = Form(...), conn = Depends(connect_db)):
    return login_s(request, username, password, redirect, conn)

@router.post("/register")
async def register(request: Request, firstname: str = Form(...), lastname: str = Form(...), username: str = Form(...), email: str = Form(...), password: str = Form(...), password_repeat: str = Form(...), redirect: str = Form(...), conn = Depends(connect_db)):
    return register_s(request, firstname, lastname, username, email, password, password_repeat, redirect, conn)

@router.get("/activate/{uuid}")
async def activate_account(request: Request, uuid: str, conn = Depends(connect_db)):
    return activate_account_s(uuid, conn)

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

class RenameData(BaseModel):
    new_username: str
    redirect: bool = False

@router.patch("/name/{username}")
async def change_name(request: Request, username: str, rename_data: RenameData, user_roles: Dict[str, List[str]] = Depends(protect_renameusers), conn = Depends(connect_db)):
    """Required right: renameusers"""
    return rename_s(request, username, rename_data.new_username, rename_data.redirect, conn)

@router.post("/block/{username}")
async def block_user(request: Request, username: str, block_until: str = Body(...), withdrawn_rights: List[str] = Body(...), permanent: bool = Body(False), reason: str = Body(...), user_roles: Dict[str, List[str]] = Depends(protect_block), conn = Depends(connect_db)):
    """Required right: userrights"""
    return block_user_s(request, username, block_until, withdrawn_rights, permanent, reason, conn)

@router.get("/block/{username}")
async def get_block_info(request: Request, username: str, user_roles: Dict[str, List[str]] = Depends(protect_read), conn = Depends(connect_db)):
    """Required right: read"""
    return get_block_info_s(request, username, conn)

@router.post("/email/{username}")
async def send_email(request: Request, username: str, message: str = Body(...), user_roles: Dict[str, List[str]] = Depends(protect_read), conn = Depends(connect_db)):
    """Required right: read"""
    return send_email_s(request, username, message, conn)