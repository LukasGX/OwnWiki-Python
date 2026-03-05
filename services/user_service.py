import base64
import json
import os
import sqlite3
from typing import Any, Dict
import uuid
from fastapi import Request, status
from fastapi.responses import RedirectResponse
from api.v1.deps import connect_db, send_email
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

def register_s(request: Request, firstname: str, lastname: str, username: str, email: str, password: str, password_repeat: str, redirect: str, conn):
    if password != password_repeat:
        return {"error": "Passwords do not match"}

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    existing_user = cursor.fetchone()

    if existing_user is not None:
        return {"error": "Username already exists"}

    password_hash = get_encrypted(password)

    user_uuid = str(uuid.uuid4())

    with open(f"registrations/{user_uuid}.json", "w") as f:
        json.dump({
            "uuid": user_uuid,
            "firstname": firstname,
            "lastname": lastname,
            "username": username,
            "email": email,
            "password_hash": password_hash
        }, f)

    with open("resources/ownwiki-logo-mini.png", "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode('utf-8')

    logo_src = f"data:image/png;base64,{encoded}"

    with open("email_templates/registration.html", "r") as f:
        email_body = f.read().format(
            SITENAME="OwnWiki",
            FIRSTNAME=firstname,
            USERNAME=username,
            ACTIVATION_LINK=f"http://localhost:8000/activate_account/{user_uuid}", # for now with localhost
            SUPPORT_EMAIL="support@ownwiki.org",
            YEAR=2026,
            FOOTER_LINK="ownwiki.org",
            LOGO_SRC=logo_src
        )

    send_email(
        subject="OwnWiki Registrierung",
        body=email_body,
        recipients=[email]
    )

    return RedirectResponse(
        url="/login",
        status_code=status.HTTP_302_FOUND
    )

def activate_account_s(uuid: str, conn):
    # check if uuid exists in registrations
    try:
        with open(f"registrations/{uuid}.json", "r") as f:
            registration_data = json.load(f)
    except FileNotFoundError:
        return {"error": "Invalid activation link"}

    # create user in database
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password_hash, roles, firstname, lastname, email) VALUES (?, ?, ?, ?, ?, ?)", (
            registration_data["username"],
            registration_data["password_hash"],
            "default;user",
            registration_data["firstname"],
            registration_data["lastname"],
            registration_data["email"]
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        return {"error": "Username or E-Mail already exists"}

    # delete registration file
    try:
        os.remove(f"registrations/{uuid}.json")
    except Exception:
        pass

    return RedirectResponse(url="/login?justActivated",status_code=302)

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

def rename_s(request: Request, username: str, new_username: str, redirect: bool, conn):
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, username))
        
        if cursor.rowcount == 0:
            return {"status": "error", "message": f"User '{username}' not found"}
        
        conn.commit()

        # rename json
        old_path_json = f"pages/user/{username}.json"
        new_path_json = f"pages/user/{new_username}.json"
        if os.path.exists(old_path_json):
            os.rename(old_path_json, new_path_json)
        # change title
        if os.path.exists(new_path_json):
            with open(new_path_json, "r") as f:
                data = json.load(f)
            data["title"] = f"Benutzer: {new_username}"
            with open(new_path_json, "w") as f:
                json.dump(data, f)
        # rename md
        old_path_md = f"pages/user/{username}.md"
        new_path_md = f"pages/user/{new_username}.md"
        if os.path.exists(old_path_md):
            os.rename(old_path_md, new_path_md)

        if request.session.get("username") == username:
            update_session(request, new_username, conn)
        
        if redirect: return RedirectResponse(url=f"/wiki/user:{new_username}", status_code=302)
        return {"status": "success", "new_username": new_username}
    except sqlite3.IntegrityError:
        return {"status": "error", "message": f"Username '{new_username}' already exists"}
    except sqlite3.Error as e:
        conn.rollback()
        return {"status": "error", "message": f"DB error: {str(e)}"}
    finally:
        conn.close()