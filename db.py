import sqlite3
import os
from pathlib import Path
from typing import Optional
from colorama import Fore

DB_PATH = Path("data/ownwiki.db")
DB_DIR = DB_PATH.parent

# create folder is not exists
DB_DIR.mkdir(parents=True, exist_ok=True)

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            roles TEXT NOT NULL
        );
    """)
    
    conn.commit()
    
    # Standard admin user (Password: admin123)
    try:
        cursor.execute(
            "INSERT INTO users (firstname, lastname, username, email, password_hash, roles) VALUES (?, ?, ?, ?, ?, ?)",
            ("-", "-", "admin", "admin@ownwiki.local", "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9", "[\"admin\"]")
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    
    conn.close()
    print(Fore.YELLOW + f"[OwnWiki] DB initialised: {DB_PATH}" + Fore.RESET)