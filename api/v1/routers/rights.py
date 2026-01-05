from fastapi import APIRouter, Depends, Form, Request
from api.v1.deps import connect_db
from services.rights_service import get_rights_by_role

router = APIRouter()

@router.get("/{role}")
async def get_rights(request: Request, role: str):
    return get_rights_by_role(role)