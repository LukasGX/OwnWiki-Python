from fastapi import Depends, Header, HTTPException, status, Request
from contextlib import asynccontextmanager
import sqlite3
from typing import List, Optional, Dict, Any
from fastapi.security.api_key import APIKeyHeader
import secrets
import hashlib


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
DB_PATH = "data/ownwiki.db"


def connect_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


@asynccontextmanager
async def get_db(request: Request):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


async def protect(
    request: Request,
    api_key: Optional[str] = Depends(api_key_header),
    required_rights: Optional[List[str]] = None
) -> Dict[str, List[str]]:
    """Protect endpoint with optional rights checking.

    Args:
        request: FastAPI Request object
        api_key: Optional API key from X-API-Key header
        required_rights: Optional list of rights required for access

    Returns:
        Dictionary with user roles: {"roles": ["role1", "role2"]}

    Raises:
        HTTPException: 401 if not authenticated, 403 if missing required rights
    """
    if api_key:
        if not await validate_api_key(api_key, request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Ungültiger oder inaktiver API-Key"
            )
        return {"roles": ["*"]}

    # session user
    session = request.session
    username = session.get("username")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login oder gültiger API-Key erforderlich"
        )

    rolesr: List[str] = session.get("roles", [])
    if not rolesr:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Rollen in Session - Rechte unklar"
        )
    
    roles = rolesr[0].split(";")

    # Check required rights if specified
    if required_rights:
        from services.rights_service import get_rights_by_role

        # Get all rights for the user's roles
        user_rights = {}
        for role in roles:
            role_rights = get_rights_by_role(role)
            user_rights.update(role_rights)

        # Check if user has all required rights
        missing_rights = []
        for right in required_rights:
            if not user_rights.get(right, False):
                missing_rights.append(right)

        if missing_rights:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Benötigte Rechte fehlen: {', '.join(missing_rights)}"
            )

    return {"roles": roles}

def protect_with_rights(required_rights: List[str]):
    """Factory function to create protect dependencies with specific rights.

    This creates a proper FastAPI dependency function that can be introspected
    for OpenAPI schema generation.

    Args:
        required_rights: List of rights required for access

    Returns:
        A dependency function that can be used with FastAPI's Depends
    """
    async def dependency(request: Request, api_key: Optional[str] = Depends(api_key_header)) -> Dict[str, List[str]]:
        return await protect(request, api_key, required_rights)

    # Copy docstring and add rights information
    dependency.__doc__ = f"""Protect endpoint requiring rights: {', '.join(required_rights)}.

    Args:
        request: FastAPI Request object
        api_key: Optional API key from X-API-Key header

    Returns:
        Dictionary with user roles: {{"roles": ["role1", "role2"]}}

    Raises:
        HTTPException: 401 if not authenticated, 403 if missing required rights
    """
    return dependency


async def validate_api_key(key: str, request: Request) -> bool:
    async with get_db(request) as conn:
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        cursor = conn.execute(
            """
            SELECT active, user_id FROM api_keys
            WHERE key_hash = ? AND active = 1
            """,
            (key_hash,)
        )
        row = cursor.fetchone()
        return row is not None
