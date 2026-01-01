from fastapi import Depends, FastAPI, HTTPException, Request, Path
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import db

from colorama import init, Fore

# import routers
from api.v1.routers import articles, user

# import services
from services.article_service import return_article

# import middleware
from sessions import init_middleware, get_session_data, set_session_data

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

app.mount("/css", StaticFiles(directory="css"), name="css")
app.mount("/js", StaticFiles(directory="js"), name="js") 
app.mount("/fonts", StaticFiles(directory="fonts"), name="fonts")
app.mount("/font-awesome", StaticFiles(directory="font-awesome"), name="font-awesome")
app.mount("/resources", StaticFiles(directory="resources"), name="resources")
app.mount("/pages", StaticFiles(directory="pages"), name="pages")


templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root():
    raise HTTPException(status_code=404, detail="Not found")

@app.get("/whoami")
async def whoami(request: Request):
    session = get_session_data(request)
    return {"username": session.get("username", "Anonymous")}

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    context = {
        "request": request
    }
    return templates.TemplateResponse("login.html", context)

@app.get("/wiki/{page}", response_class=HTMLResponse)
async def wiki_page(request: Request, page: str = Path(..., min_length=1)):
    if ":" not in page:
        raise HTTPException(400, f"Invalid page format '{page}'. Use 'namespace:name' format.")
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

    context = {
        "request": request,
        "title": data["title"],
        "content": data["content"],
        "logged_in": logged_in,
        "username": session.get("username", "Anonymous"),
        "is_admin": False,
        "controls": data["noControls"] == False,
        "protected": data["protected"],
        "needed_right": needed_right,
        "page": page,
        "permissions": {
            "edit": True
        },
    }
    return templates.TemplateResponse("read.html", context)