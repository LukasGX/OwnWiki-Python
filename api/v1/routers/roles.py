from fastapi import APIRouter, Depends, Form, Request
from api.v1.deps import protect_with_rights
from services.roles_service import get_role_color, get_role_name
from typing import Dict, List

router = APIRouter()

protect_read = protect_with_rights(["read"])

@router.get("/{role}/color")
async def get_color(request: Request, role: str, user_roles: Dict[str, List[str]] = Depends(protect_read)):
    """Required right: read"""
    return get_role_color(role)

@router.get("/{role}/name")
async def get_name(request: Request, role: str, user_roles: Dict[str, List[str]] = Depends(protect_read)):
    """Required right: read"""
    return get_role_name(role)