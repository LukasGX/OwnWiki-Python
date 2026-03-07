import os

from fastapi import APIRouter, Depends, Form, Request
from api.v1.deps import protect_with_rights
from services.search_service import search_s
from typing import Dict, List

router = APIRouter()

protect_read = protect_with_rights(["read"])

@router.get("/")
async def search(
    request: Request,
    q: str,
    namespace: str = None,
    page: int = 1,
    limit: int = 20,
    user_roles: Dict[str, List[str]] = Depends(protect_read)
):
    """Required right: read"""
    return search_s(request, q, namespace, page, limit)