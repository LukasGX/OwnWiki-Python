import re
from fastapi import Depends, FastAPI, HTTPException, Request, Path
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import db

from colorama import init, Fore

# import routers
from api.v1.routers import articles, user, roles

# import services
from services.article_service import return_article
from services.roles_service import get_role_color, get_role_name
from services.user_service import update_session

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

app.mount("/css", StaticFiles(directory="css"), name="css")
app.mount("/js", StaticFiles(directory="js"), name="js") 
app.mount("/fonts", StaticFiles(directory="fonts"), name="fonts")
app.mount("/font-awesome", StaticFiles(directory="font-awesome"), name="font-awesome")
app.mount("/resources", StaticFiles(directory="resources"), name="resources")
app.mount("/pages", StaticFiles(directory="pages"), name="pages")
app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root():
    raise HTTPException(status_code=404, detail="Not found")

@app.get("/whoami")
async def whoami(request: Request, conn = Depends(connect_db)):
    update_session(request, request.session.get("username", ""), conn)
    session = get_session_data(request)
    return {"username": session.get("username", "Anonymous")}

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    context = {
        "request": request
    }
    return templates.TemplateResponse("login.html", context)

@app.get("/wiki/{page}", response_class=HTMLResponse)
async def wiki_page(request: Request, page: str = Path(..., min_length=1), conn = Depends(connect_db)):
    if ":" not in page:
        raise HTTPException(400, f"Invalid page format '{page}'. Use 'namespace:name' format.")
    
    update_session(request, request.session.get("username", ""), conn)

    splitted = page.split(":")
    data = return_article(splitted[0], splitted[1])

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

    context = {
        "request": request,
        "title": data["title"],
        "content": data["content"],
        "logged_in": logged_in,
        "username": session.get("username", "Anonymous"),
        "is_admin": is_admin,
        "controls": data["noControls"] == False,
        "protected": data["protected"],
        "needed_right": needed_right,
        "page": page,
        "permissions": {
            "edit": True
        },
    }
    return templates.TemplateResponse("read.html", context)

@app.get("/account", response_class=HTMLResponse)
async def wiki_page(request: Request, conn = Depends(connect_db)):
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
        "logged_in": logged_in,
        "username": session.get("username", "Anonymous"),
        "firstname": session.get("firstname", ""),
        "lastname": session.get("lastname", ""),
        "email": session.get("email", ""),
        "is_admin": is_admin,
        "roles": (roles or rolesr),
        "role_colors": role_colors,
        "role_names": role_names,
        "permissions": {
            "edit": True
        },
    }
    return templates.TemplateResponse("account.html", context)

@app.get("/wiki/{page}/edit", response_class=HTMLResponse)
async def edit_page(request: Request, page: str = Path(..., min_length=1), conn = Depends(connect_db)):
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

    if "admin" in session:
        is_admin = True
    else:
        is_admin = False

    content = data["content"].lstrip("\t ")

    context = {
        "request": request,
        "title": data["title"],
        "content": content,
        "logged_in": logged_in,
        "username": session.get("username", "Anonymous"),
        "is_admin": is_admin,
        "controls": data["noControls"] == False,
        "protected": data["protected"],
        "needed_right": needed_right,
        "page": page,
        "permissions": {
            "edit": True
        },
    }
    return templates.TemplateResponse("edit.html", context)