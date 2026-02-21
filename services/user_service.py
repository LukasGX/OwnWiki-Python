import json
import sqlite3
from typing import Any, Dict
from fastapi import Request, status
from fastapi.responses import RedirectResponse
from api.v1.deps import connect_db
from sessions import set_session_data, clear_session
from argon2 import PasswordHasher

ph = PasswordHasher()

def get_encrypted(input: str):
    hashed = ph.hash(input)
    return hashed

def login_s(request: Request, username: str, password: str, redirect: str, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user is None:
        return {"error": "Invalid username or password"}
    
    try:
        ph.verify(user["password_hash"], password)
    except:
        return {"error": "Invalid username or password"}


    # create session data
    try:
        set_session_data(request, username, user["roles"], user["firstname"], user["lastname"], user["email"])
    except Exception:
        # no fallback
        pass

    # store roles (normalize to list)
    roles = user.get("roles") if isinstance(user, dict) else user["roles"]
    if isinstance(roles, str):
        roles_list = [r.strip() for r in roles.split(",") if r.strip()]
    else:
        roles_list = list(roles) if roles is not None else []

    request.session["roles"] = roles_list
    request.session["logged_in"] = True
    request.session["is_admin"] = "admin" in roles_list

    if redirect == "true":
        return RedirectResponse(
            url="/wiki/main:main",
            status_code=status.HTTP_302_FOUND
        )
    return {"status": "logged_in", "user": username, "roles": roles_list}

def update_session(request: Request, username: str, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user is None:
        return {"error": "User not found"}

    try:
        set_session_data(request, username, user["roles"], user["firstname"], user["lastname"], user["email"])
    except Exception:
        pass

    # store roles (normalize to list)
    roles = user.get("roles") if isinstance(user, dict) else user["roles"]
    if isinstance(roles, str):
        roles_list = [r.strip() for r in roles.split(",") if r.strip()]
    else:
        roles_list = list(roles) if roles is not None else []

    request.session["roles"] = roles_list
    request.session["logged_in"] = True
    request.session["is_admin"] = "admin" in roles_list

    return {"status": "session_updated", "user": username, "roles": roles_list}

def logout_s(request: Request):
    try:
        clear_session(request)
    except Exception:
        pass
    return {"status": "logged_out"}

def get_roles_s(username: str):
    conn = sqlite3.connect("data/ownwiki.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT roles FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return {"error": "User not found"}

    roles = row["roles"] if isinstance(row, (dict, sqlite3.Row)) else row[0]

    roles_list = []
    if roles is None:
        roles_list = []
    else:
        roles_list = roles.split(";")

    return {"user": username, "roles": roles_list}

def change_roles_s(username: str, roles_dict: Dict[str, bool]) -> Dict[str, Any]:
    conn = sqlite3.connect("data/ownwiki.db", check_same_thread=False)
    cursor = conn.cursor()
    
    try:
        active_roles = [role for role, active in roles_dict.items() if active]
        roles_string = ';'.join(active_roles)
        
        cursor.execute(
            "UPDATE users SET roles = ? WHERE username = ?",
            (roles_string, username)
        )
        
        cursor.execute("SELECT id, roles FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if cursor.rowcount == 0:
            return {"status": "error", "message": f"User '{username}' nicht gefunden"}
        
        conn.commit()
        return {
            "status": "success", 
            "roles": roles_string,
            "user_id": user[0]
        }
        
    except sqlite3.Error as e:
        conn.rollback()
        return {"status": "error", "message": f"DB Fehler: {str(e)}"}
    
    finally:
        conn.close()