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
    api_key: Optional[str] = Depends(api_key_header)
) -> Dict[str, List[str]]:
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
    
    roles: List[str] = session.get("roles", [])
    if not roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Rollen in Session - Rechte unklar"
        )
    
    return {"roles": roles}


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
