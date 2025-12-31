from fastapi import FastAPI, HTTPException, Request, Path
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# import routers
from api.v1.routers import articles

# import services
from services.article_service import return_article

app = FastAPI(title="OwnWiki")

app.include_router(articles.router, prefix="/api/v1/articles", tags=["articles"])

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

    context = {
        "request": request,
        "title": data["title"],
        "content": data["content"],
        "logged_in": False,
        "is_admin": False,
        "controls": True,
        "permissions": {
            "edit": True
        },
    }
    return templates.TemplateResponse("read.html", context)