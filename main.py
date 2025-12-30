from fastapi import FastAPI, HTTPException, Request, Path
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/css", StaticFiles(directory="css"), name="css")
app.mount("/js", StaticFiles(directory="js"), name="js") 
app.mount("/fonts", StaticFiles(directory="fonts"), name="fonts")
app.mount("/font-awesome", StaticFiles(directory="font-awesome"), name="font-awesome")
app.mount("/resources", StaticFiles(directory="resources"), name="resources")

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root():
    raise HTTPException(status_code=404, detail="Not found")

@app.get("/wiki/{page}", response_class=HTMLResponse)
async def wiki_page(request: Request, page: str = Path(..., min_length=1)):
    content = f"Inhalt der Seite '{page}'"
    
    context = {
        "request": request,
        "title": page,
        "logged_in": False,
        "is_admin": False,
        "controls": True,
        "permissions": {
            "edit": True
        },
    }
    return templates.TemplateResponse("read.html", context)