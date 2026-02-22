from datetime import datetime
from babel.dates import format_datetime
import json
import re
from fastapi import Depends, FastAPI, HTTPException, Request, Path
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import db

from colorama import init, Fore

# import routers
from api.v1.routers import articles, user, roles, rights, debug

# import services
from services.article_service import return_article, return_discussion
from services.roles_service import get_role_color, get_role_name
from services.user_service import update_session, get_roles_s
from services.rights_service import get_rights_by_role

# import middleware
from sessions import init_middleware, get_session_data

# import deps
from api.v1.deps import connect_db

init()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db.init_db()
    print(Fore.YELLOW + "[OwnWiki] Server started" + Fore.RESET)
    yield
    # Shutdown
    print(Fore.YELLOW + "[OwnWiki] Server stopped" + Fore.RESET)

app = FastAPI(title="OwnWiki", lifespan=lifespan)

# Initialize session middleware
init_middleware(app)

app.include_router(articles.router, prefix="/api/v1/articles", tags=["articles"])
app.include_router(user.router, prefix="/api/v1/user", tags=["user"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["roles"])
app.include_router(rights.router, prefix="/api/v1/rights", tags=["rights"])
app.include_router(debug.router, prefix="/api/v1/debug", tags=["debug"])

app.mount("/css", StaticFiles(directory="css"), name="css")
app.mount("/js", StaticFiles(directory="js"), name="js") 
app.mount("/fonts", StaticFiles(directory="fonts"), name="fonts")
app.mount("/font-awesome", StaticFiles(directory="font-awesome"), name="font-awesome")
app.mount("/resources", StaticFiles(directory="resources"), name="resources")
app.mount("/pages", StaticFiles(directory="pages"), name="pages")
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

def get_user_rights(request: Request):
    user_rights = {}
    for role in request.session.get("roles", ["default"])[0].split(";"):
        rights = get_rights_by_role(role)
        for right, value in rights.items():
            user_rights[right] = value

    # fill missing rights with False
    with open("static/rightlist.json", "r", encoding="utf-8") as f:
        all_rights = json.load(f)

    for right in all_rights:
        if right not in user_rights:
            user_rights[right] = False

    return user_rights

def parse_chat(content: list) -> list:
    for item in content:
        for message in item["messages"]:
            ts = message["timestamp"]
            if ts.endswith("Z"):
                iso_ts = ts[:-1] + "+00:00"
            else:
                iso_ts = ts
                
            dt = datetime.fromisoformat(iso_ts)
            message["formatted_time"] = dt.strftime("%d.%m.%Y, %H:%M")
    
    return content


@app.get("/")
async def root():
    return RedirectResponse(url="/wiki/main:main", status_code=302)

@app.get("/whoami")
async def whoami(request: Request, conn = Depends(connect_db)):
    """
    Short overview of what data is known about the logged in user.
    """
    update_session(request, request.session.get("username", ""), conn)
    session = get_session_data(request)
    return {"username": session.get("username", "Anonymous")}

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    The OwnWiki login page.
    """
    context = {
        "request": request
    }
    return templates.TemplateResponse("login.html", context)

@app.get("/register", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    The OwnWiki account creation page.
    """
    context = {
        "request": request
    }
    return templates.TemplateResponse("register.html", context)

@app.get("/wiki/{page}", response_class=HTMLResponse)
async def wiki_page(request: Request, page: str = Path(..., min_length=1), conn = Depends(connect_db)):
    """
    The page where you can view any page in the wiki.
    """
    if ":" not in page:
        raise HTTPException(400, f"Invalid page format '{page}'. Use 'namespace:name' format.")
    
    update_session(request, request.session.get("username", ""), conn)

    splitted = page.split(":")
    data = return_article(splitted[0], splitted[1])

    error = data.get("error")
    if error is not None and error == "404":
        request.session["redirect_data"] = {"page": page}
        return RedirectResponse(url="/404", status_code=302)


    session = get_session_data(request)
    if "username" in session:
        logged_in = True
    else:
        logged_in = False

    # get needed right
    if data["protected"] == "none":
        needed_right = "edit"
    elif data["protected"] == "semiprotected":
        needed_right = "editsemiprotected"
    elif data["protected"] == "protected":
        needed_right = "editprotected"
    elif data["protected"] == "superprotected":
        needed_right = "editsuperprotected"
    else:
        needed_right = "edit" # fallback

    roles: list = request.session.get("roles", [])

    if len(roles) > 0 and "admin" in roles[0].split(";"):
        is_admin = True
    else:
        is_admin = False

    if splitted[0] == "user":
        try:
            user_roles = get_roles_s(splitted[1])
        except:
            user_roles = []
    else:
        user_roles = []

    user_rights = get_user_rights(request)
    needed_right = "read"

    if needed_right not in user_rights or not user_rights[needed_right]:
        request.session["redirect_data"] = {
            "page": page,
            "right": needed_right
        }
        return RedirectResponse(url="/403", status_code=302)
    
    if data["deleted"] == True:
        if user_rights["browsedeleted"] == True:
            show = True
        else: show = False
    else:
        show = True
    
    content = data["content"]

    match = re.search(r'\$\$REDIRECT:([^:]+):([^:]+)\$\$', content)

    if match:
        ns, name = match.groups()
        return RedirectResponse(url=f"/wiki/{ns}:{name}", status_code=302)

    context = {
        "request": request,
        "title": data["title"],
        "content": content,
        "controls": data["noControls"] == False,
        "protected": data["protected"],
        "needed_right": needed_right,
        "permissions": user_rights,
        "deleted": data["deleted"],
        "deluser": data["deletionInfo"]["user"],
        "show": show,
        "ns": splitted[0],
        "user_roles": user_roles,

        "logged_in": logged_in,
        "username": session.get("username", "Anonymous"),
        "is_admin": is_admin,
        "page": page
    }
    return templates.TemplateResponse("read.html", context)

@app.get("/account", response_class=HTMLResponse)
async def account_page(request: Request, conn = Depends(connect_db)):
    """
    Overview your account.
    """
    update_session(request, request.session.get("username", ""), conn)

    session = get_session_data(request)
    if "username" in session:
        logged_in = True
    else:
        logged_in = False
        return RedirectResponse(
            url="/login",
            status_code=302)

    rolesr: list = request.session.get("roles", [])

    if len(rolesr) > 0 and "admin" in rolesr[0].split(";"):
        is_admin = True
        roles = rolesr[0].split(";")
    else:
        is_admin = False
        roles = rolesr[0].split(";")

    # role colors
    role_colors = {}
    for role in roles:
        role = role.strip()
        color = get_role_color(role)
        role_colors[role] = color

    # role names
    role_names = {}
    for role in roles:
        role = role.strip()
        name = get_role_name(role)
        role_names[role] = name

    context = {
        "request": request,
        "firstname": session.get("firstname", ""),
        "lastname": session.get("lastname", ""),
        "email": session.get("email", ""),
        "is_admin": is_admin,
        "roles": (roles or rolesr),
        "role_colors": role_colors,
        "role_names": role_names,

        "logged_in": logged_in,
        "username": session.get("username", "Anonymous")
    }
    return templates.TemplateResponse("account.html", context)

@app.get("/users", response_class=HTMLResponse)
async def all_users(request: Request, conn = Depends(connect_db)):
    """
    List of all users.
    """
    update_session(request, request.session.get("username", ""), conn)

    session = get_session_data(request)
    if "username" in session:
        logged_in = True
    else:
        logged_in = False

    rolesr: list = request.session.get("roles", [])
    try:
        roless = rolesr[0].split(";")
    except:
        roless = ["default"]

    if len(rolesr) > 0 and "admin" in roless: is_admin = True
    else: is_admin = False

    user_rights = get_user_rights(request)

    users = []

    cursor = conn.cursor()
    cursor.execute("""
        SELECT username, firstname, roles 
        FROM users 
        ORDER BY id 
        LIMIT 50
    """)

    for row in cursor.fetchall():
        username, firstname, roles_str = row
        
        roles = [r.strip() for r in roles_str.split(';') if r.strip()]
        
        users.append({
            "username": username,
            "firstname": firstname,
            "roles": roles
        })

    conn.close()

    # role colors
    role_colors = {
        "admin": "#FFC8C8",
        "interface-admin": "#FFC8C8",
        "bureaucrat": "#FFC8C8",
        "oversighter": "#FFC8C8",
        "ownwiki-admin": "#FF8686",
        "bot": "#C3C3FF"
    }

    # role names
    role_names = {
        "default": "Standard",
        "user": "Benutzer",
        "autoconfirmed": "Automatisch bestätigt",
        "bot": "Bot",
        "admin": "Administrator",
        "interface-admin": "UI-Administrator",
        "bureaucrat": "Bürokrat",
        "oversighter": "Oversighter",
        "ownwiki-admin": "OwnWiki-Administrator"
    }

    context = {
        "request": request,
        "is_admin": is_admin,
        "role_colors": role_colors,
        "role_names": role_names,

        "permissions": user_rights,

        "logged_in": logged_in,
        "users": users
    }
    return templates.TemplateResponse("users.html", context)

@app.get("/wiki/{page}/edit", response_class=HTMLResponse)
async def edit_page(request: Request, page: str = Path(..., min_length=1), conn = Depends(connect_db)):
    """
    Edit any page in the wiki.
    """
    if ":" not in page:
        raise HTTPException(400, f"Invalid page format '{page}'. Use 'namespace:name' format.")
    
    update_session(request, request.session.get("username", ""), conn)

    splitted = page.split(":")
    data = return_article(splitted[0], splitted[1], True)

    session = get_session_data(request)
    if "username" in session:
        logged_in = True
    else:
        logged_in = False

    user_rights = get_user_rights(request)

    # get needed right
    if data["deleted"] == True:
        needed_right = "browsedeleted"
    elif logged_in and splitted[0] == "user":
        if session["username"] == splitted[1]: needed_right = "edit"
        else: needed_right = "editprotected"
    else:
        match data["protected"]:
            case "none": needed_right = "edit"
            case "semiprotected": needed_right = "editsemiprotected"
            case "protected": needed_right = "editprotected"
            case "superprotected": needed_right = "editsuperprotected"
            case _: needed_right = "edit"

    if needed_right not in user_rights or not user_rights[needed_right]:
        p = f"{page}/edit"

        request.session["redirect_data"] = {
            "page": p,
            "right": needed_right
        }
        return RedirectResponse(url="/403", status_code=302)

    if "admin" in session:
        is_admin = True
    else:
        is_admin = False

    content = data["content"].lstrip("\t ")

    context = {
        "request": request,
        "title": data["title"],
        "content": content,
        "controls": data["noControls"] == False,
        "protected": data["protected"],
        "needed_right": needed_right,
        "permissions": user_rights,

        "logged_in": logged_in,
        "username": session.get("username", "Anonymous"),
        "is_admin": is_admin,
        "page": page,
    }
    return templates.TemplateResponse("edit.html", context)

@app.get("/wiki/{page}/create", response_class=HTMLResponse)
async def create_page(request: Request, page: str = Path(..., min_length=1), conn = Depends(connect_db)):
    """
    Create a new page in the wiki.
    """
    if ":" not in page:
        raise HTTPException(400, f"Invalid page format '{page}'. Use 'namespace:name' format.")
    
    update_session(request, request.session.get("username", ""), conn)

    splitted = page.split(":")
    data = return_article(splitted[0], splitted[1], True)

    error = data.get("error")
    if error is None or not error == "404":
        return RedirectResponse(url=f"/wiki/{page}/edit", status_code=302)

    session = get_session_data(request)
    if "username" in session:
        logged_in = True
    else:
        logged_in = False

    user_rights = get_user_rights(request)

    # get needed right
    needed_right = "createpage"

    if needed_right not in user_rights or not user_rights[needed_right]:
        p = f"{page}/edit"

        request.session["redirect_data"] = {
            "page": p,
            "right": needed_right
        }
        return RedirectResponse(url="/403", status_code=302)

    if "admin" in session:
        is_admin = True
    else:
        is_admin = False

    context = {
        "request": request,
        "is_admin": is_admin,
        "controls": True,
        "protected": "none",
        "needed_right": needed_right,
        "page": page,
        "permissions": user_rights,

        "logged_in": logged_in,
        "username": session.get("username", "Anonymous")
    }
    return templates.TemplateResponse("create.html", context)

@app.get("/wiki/{page}/discussion", response_class=HTMLResponse)
async def discussion_page(request: Request, page: str = Path(..., min_length=1), conn = Depends(connect_db)):
    """
    View any page discussion.
    """
    if ":" not in page:
        raise HTTPException(400, f"Invalid page format '{page}'. Use 'namespace:name' format.")
    
    update_session(request, request.session.get("username", ""), conn)

    splitted = page.split(":")
    data = return_discussion(splitted[0], splitted[1])
    articledata = return_article(splitted[0], splitted[1])

    session = get_session_data(request)
    if "username" in session:
        logged_in = True
    else:
        logged_in = False

    user_rights = get_user_rights(request)
    existing = data["found"]

    # get needed right
    if articledata["deleted"] == True:
        needed_right = "browsedeleted"
    elif existing:
        needed_right = "read"
    else:
        needed_right = "creatediscussion"

    if needed_right not in user_rights or not user_rights[needed_right]:
        p = f"{page}/discussion"

        request.session["redirect_data"] = {
            "page": p,
            "right": needed_right
        }
        return RedirectResponse(url="/403", status_code=302)

    if "admin" in session:
        is_admin = True
    else:
        is_admin = False

    if existing:
        content = parse_chat(data["content"])
    else:
        content = ""

    context = {
        "request": request,
        "content": content,
        "title": f"{articledata['title']} - Diskussion",
        "needed_right": needed_right,
        "existing": existing,
        "permissions": user_rights,

        "logged_in": logged_in,
        "username": session.get("username", "Anonymous"),
        "is_admin": is_admin,
        "page": page
    }
    return templates.TemplateResponse("discussion.html", context)

@app.get("/403", response_class=HTMLResponse)
async def forbidden_page(request: Request):
    """
    Is shown if you don't have sufficient rights to access the requested page.
    """
    redirect_data = request.session.get("redirect_data", {})
    page = redirect_data.get("page")
    right = redirect_data.get("right", "unbekannt")

    session = get_session_data(request)
    if "username" in session:
        logged_in = True
    else:
        logged_in = False

    context = {
        "request": request,
        "page": page,
        "right": right,

        "logged_in": logged_in,
        "username": session.get("username", "Anonymous")
    }
    return templates.TemplateResponse("403.html", context)

@app.get("/404", response_class=HTMLResponse)
async def page_not_found(request: Request):
    """
    Is shown if the requested page is not found.
    """
    session = get_session_data(request)
    if "username" in session:
        logged_in = True
    else:
        logged_in = False

    redirect_data = session.get("redirect_data", {})
    page = redirect_data.get("page")

    context = {
        "request": request,
        "page": page,

        "logged_in": logged_in,
        "username": session.get("username", "Anonymous")
    }
    return templates.TemplateResponse("404.html", context)