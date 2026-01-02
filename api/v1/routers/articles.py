from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel
from api.v1.deps import get_api_key
from services.article_service import return_article, save_article
from helper.gethtml import get_html

router = APIRouter()

@router.get("/{namespace}/{name}")
async def get_article(namespace: str, name: str):
    return return_article(namespace, name)

@router.get("/preview")
async def preview_article(md: str):
    return get_html(md)

class ArticleSave(BaseModel):
    namespace: str
    name: str
    content: str

@router.patch("/save")
async def edit_article(data: ArticleSave = Body(...)):
    return save_article(data.namespace, data.name, data.content)