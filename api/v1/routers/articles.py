from fastapi import APIRouter, Depends
from api.v1.deps import get_api_key
from services.article_service import return_article

router = APIRouter()

@router.get("/{namespace}/{name}")
async def get_article(namespace: str, name: str):
    return return_article(namespace, name)