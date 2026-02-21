from fastapi import APIRouter, Depends, Form, Request
from api.v1.deps import protect_with_rights
from services.rights_service import get_rights_by_role
from typing import Dict, List

router = APIRouter()

protect_read = protect_with_rights(["read"])

@router.get("/{role}")
async def get_rights(request: Request, role: str, user_roles: Dict[str, List[str]] = Depends(protect_read)):
    """Required right: read"""
    return get_rights_by_role(role)