import json
from pathlib import Path
import markdown
from fastapi import HTTPException

PAGES_DIR = Path(__file__).parent.parent / "pages"

def return_article(namespace: str, name: str):
    json_path = PAGES_DIR / f"{namespace}/{name}.json"
    md_path = PAGES_DIR / f"{namespace}/{name}.md"
    
    # check both paths
    if not json_path.exists():
        raise HTTPException(404, f"Article '{namespace}:{name}' not found")
    if not md_path.exists():
        raise HTTPException(404, f"Markdown content for '{namespace}:{name}' missing")
    
    # open safely
    json_content = json.loads(json_path.read_text(encoding="utf-8"))
    html = markdown.markdown(md_path.read_text(encoding="utf-8"))
    
    return {
        "content": html,
        "title": json_content["title"],
        "noControls": json_content.get("noControls", False),
        "protected": json_content.get("protected", "none")
    }