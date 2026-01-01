from fastapi import Depends, Header, HTTPException
from contextlib import asynccontextmanager
import sqlite3
from typing import Generator

async def get_api_key(api_key: str = Header(None)):
    return True # DUMMY IMPLEMENTATION

DB_PATH = "data/ownwiki.db"

def connect_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()