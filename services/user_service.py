import hashlib
from fastapi import Request, status
from fastapi.responses import RedirectResponse
from api.v1.deps import connect_db
from sessions import set_session_data, clear_session

def login_s(request: Request, username: str, password: str, redirect: str, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user is None:
        return {"error": "Invalid username or password"}
    
    pw_hash = password.encode('utf-8')
    pw_hash = hashlib.sha256(pw_hash).hexdigest()

    if pw_hash != user["password_hash"]:
        return {"error": "Invalid username or password"}

    # create session data
    try:
        set_session_data(request, username)
    except Exception:
        # fallback to direct session assignment if helper unavailable
        request.session["username"] = username

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

def logout_s(request: Request):
    try:
        clear_session(request)
    except Exception:
        pass
    return {"status": "logged_out"}