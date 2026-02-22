from fastapi import APIRouter, Depends, Form, Request
from api.v1.deps import protect_with_rights
from services.debug_service import generate_uuid
from typing import Dict, List

router = APIRouter()

protect_debug = protect_with_rights(["read"])

@router.get("/uuid")
async def get_uuid(request: Request, user_roles: Dict[str, List[str]] = Depends(protect_debug)):
    """Required right: debug"""
    return generate_uuid()