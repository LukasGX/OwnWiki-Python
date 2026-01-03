from fastapi import APIRouter, Depends, Form, Request
from api.v1.deps import connect_db
from services.roles_service import get_role_color

router = APIRouter()

@router.get("/{role}/color")
async def get_color(request: Request, role: str):
    return get_role_color(role)