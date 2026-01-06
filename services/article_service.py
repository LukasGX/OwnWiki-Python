import json
from pathlib import Path
from helper.gethtml import get_html
from fastapi import HTTPException

PAGES_DIR = Path(__file__).parent.parent / "pages"

def return_article(namespace: str, name: str, raw: bool = False):
    json_path = PAGES_DIR / f"{namespace}/{name}.json"
    md_path = PAGES_DIR / f"{namespace}/{name}.md"
    
    # check both paths
    if not json_path.exists():
        raise HTTPException(404, f"Article '{namespace}:{name}' not found")
    if not md_path.exists():
        raise HTTPException(404, f"Markdown content for '{namespace}:{name}' missing")
    
    # open safely
    json_content = json.loads(json_path.read_text(encoding="utf-8"))

    md_content = md_path.read_text(encoding="utf-8")
    html = get_html(md_content)
    md = md_content

    if raw:
        toReturn = md
    else:
        toReturn = html
    
    return {
        "content": toReturn,
        "title": json_content["title"],
        "noControls": json_content.get("noControls", False),
        "protected": json_content.get("protected", "none")
    }

def return_discussion(namespace: str, name: str):
    json_path = PAGES_DIR / f"{namespace}/{name}_discussion.json"
    
    # check both paths
    if not json_path.exists():
        return {"found": False}
    
    # open safely
    json_content = json.loads(json_path.read_text(encoding="utf-8"))

    return {
        "content": json_content,
        "found": True
    }

def save_article(namespace: str, name: str, content: str):
    md_path = PAGES_DIR / f"{namespace}/{name}.md"
    
    # check path
    if not md_path.exists():
        raise HTTPException(404, f"Article '{namespace}:{name}' not found")
    
    # checks for content
    # later ...
    
    # save content
    md_path.write_text(content, encoding="utf-8")
    
    return {"status": "success", "message": f"Article '{namespace}:{name}' saved successfully."}