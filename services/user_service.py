import base64
import json
import os
import re
import sqlite3
from typing import Any, Dict
import uuid
from fastapi import Request, status
from fastapi.responses import RedirectResponse
from api.v1.deps import connect_db, send_email
from sessions import set_session_data, clear_session
from argon2 import PasswordHasher
from datetime import datetime, timedelta


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

def parse_duration(input_str):
    if input_str.lower() == 'dauerhaft':
        return None
    
    input_str = input_str.replace(" ", "")
    
    total_seconds = 0
    units = {
        'j': 365 * 24 * 3600,
        'm': 30 * 24 * 3600,
        'w': 7 * 24 * 3600,
        't': 24 * 3600,
        'h': 3600,
        'min': 60
    }
    
    for match in re.finditer(r'(\d+)(min|[jwmth])', input_str.lower()):
        num = int(match.group(1))
        unit = match.group(2)
        total_seconds += num * units.get(unit, 0)
        print(f"Matched: {num}{unit}")
    
    return timedelta(seconds=total_seconds)

def block_user_s(request: Request, username: str, block_until: str, withdrawn_rights: list, is_permanent: bool, reason: str, conn):
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, firstname, email FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if user is None:
            return {"status": "error", "message": f"User '{username}' not found"}
        
        user_id = user[0]
        user_firstname = user[1]
        user_email = user[2]

        cursor.execute("SELECT id FROM users WHERE username = ?", (request.session.get("username"),))
        admin_user = cursor.fetchone()
        if admin_user is None:
            return {"status": "error", "message": "Admin user not found"}
        
        admin_id = admin_user[0]

        cursor.execute("SELECT id FROM blocks WHERE user_id = ?", (user_id,))
        existing_block = cursor.fetchone()

        # parse block_until to correct format
        time_delta = parse_duration(block_until)
        expiry = datetime.now() + time_delta

        if existing_block:
            cursor.execute("""
                UPDATE blocks 
                SET block_until = ?, withdrawnRights = ?, is_permanent = ?, admin_id = ?, reason = ?
                WHERE user_id = ?
            """, (expiry, ';'.join(withdrawn_rights), is_permanent, admin_id, reason, user_id))
        else:
            cursor.execute("""
                INSERT INTO blocks (user_id, block_until, withdrawnRights, is_permanent, admin_id, reason) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, expiry, ';'.join(withdrawn_rights), is_permanent, admin_id, reason))
        
        conn.commit()

        # send mail to user
        with open("resources/ownwiki-logo-mini.png", "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')

        logo_src = f"data:image/png;base64,{encoded}"
        block_type = "dauerhaft" if is_permanent else f"vorübergehend"
        end_string = "" if is_permanent else f"<span class='fat'>Ablauf der Sperre:</span> {expiry.strftime("%d.%m.%Y %H:%M:%S")}<br />"
        expiry_note = "" if is_permanent else f"Die Sperre läuft automatisch ab. Danach steht Ihnen Ihr Konto wieder voll zur Verfügung."

        with open("email_templates/block.html", "r") as f:
            email_body = f.read().format(
                SITENAME="OwnWiki",
                FIRSTNAME=user_firstname,
                USERNAME=username,
                SUPPORT_EMAIL="support@ownwiki.org",
                YEAR=2026,
                FOOTER_LINK="ownwiki.org",
                REASON=reason,
                BLOCK_TYPE=block_type,
                BLOCK_ADMIN=request.session.get("username"),
                END_STRING=end_string,
                EXPIRY_NOTE=expiry_note,
                LOGO_SRC=logo_src
            )

        send_email(
            subject="OwnWiki-Konto gesperrt",
            body=email_body,
            recipients=[user_email]
        )

        return {"status": "success", "message": f"User '{username}' has been blocked until {block_until}"}
    except sqlite3.Error as e:
        conn.rollback()
        return {"status": "error", "message": f"DB error: {str(e)}"}
    finally:
        conn.close()

def send_email_s(request: Request, username: str, message: str, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user is None:
        return {"status": "error", "message": f"User '{username}' not found"}

    recipient_email = user[0]

    sender_username = request.session.get("username", "Unbekannt")

    with open("resources/ownwiki-logo-mini.png", "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode('utf-8')

    logo_src = f"data:image/png;base64,{encoded}"

    with open("email_templates/usermsg.html", "r") as f:
        email_body = f.read().format(
            SITENAME="OwnWiki",
            USERNAME=username,
            SUPPORT_EMAIL="support@ownwiki.org",
            YEAR=2026,
            FOOTER_LINK="ownwiki.org",
            SENDING_USER=sender_username,
            MESSAGE=message,
            LOGO_SRC=logo_src
        )

    send_email(
        subject="OwnWiki - Neue Nachricht von " + sender_username,
        body=email_body,
        recipients=[recipient_email]
    )

    return {"status": "success", "message": f"Message sent to '{username}'"}

def get_block_info_s(request: Request, username: str, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user is None:
        return {"status": "error", "message": f"User '{username}' not found"}

    user_id = user[0]

    cursor.execute("""
                   SELECT
                   block_until,
                   withdrawnRights,
                   is_permanent,
                   reason,
                   u.username as admin_username
                   FROM blocks b
                   LEFT JOIN users u ON b.admin_id = u.id
                   WHERE user_id = ?
                   """, (user_id,))
    block_info = cursor.fetchone()

    if block_info is None:
        return {"status": "success", "blocked": False}

    block_until, withdrawn_rights, is_permanent, reason, admin_username = block_info
    blocked = True

    return {
        "status": "success",
        "blocked": blocked,
        "block_until": block_until,
        "withdrawn_rights": withdrawn_rights.split(";") if withdrawn_rights else [],
        "is_permanent": bool(is_permanent),
        "reason": reason,
        "admin": admin_username
    }