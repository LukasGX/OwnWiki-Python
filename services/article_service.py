import json
import os
from pathlib import Path
from helper.gethtml import get_html
from fastapi import HTTPException

PAGES_DIR = Path(__file__).parent.parent / "pages"

def return_article(namespace: str, name: str, raw: bool = False):
    json_path = PAGES_DIR / f"{namespace}/{name}.json"
    md_path = PAGES_DIR / f"{namespace}/{name}.md"
    
    # check both paths
    if not json_path.exists():
        return {"error": "404"}
    if not md_path.exists():
        return {"error": "404"}
    
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
        "protected": json_content.get("protected", "none"),
        "deleted": json_content.get("deleted", False),
        "deletionInfo": {
            "user": json_content.get("deletionInfo", {}).get("user", "")
        }
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

def create_article_s(namespace: str, name: str, title: str, content: str, throw: bool = True):
    md_path = PAGES_DIR / f"{namespace}/{name}.md"
    json_path = PAGES_DIR / f"{namespace}/{name}.json"
    ns_path = PAGES_DIR / namespace

    # check ns
    if not os.path.isdir(ns_path):
        if throw: raise HTTPException(status_code=400, detail="Wrong namespace")
        else: return {"error": "Wrong namespace"}

    if md_path.exists():
        if throw: raise HTTPException(status_code=409, detail="Page already existing")
        else: return {"error": "Page already existing"}
    
    if json_path.exists():
        if throw: raise HTTPException(status_code=409, detail="Page already existing")
        else: return {"error": "Page already existing"}
    
    # checks for content
    # later ...

    with open(md_path, "x") as f:
        f.write(content)

    with open(json_path, "x") as f:
        f.write(json.dumps({"title": title, "noControls": False, "protected": "none", "deleted": False, "deletionInfo": {"user": ""}}, indent=4))

    return {"status": "success", "message": f"Article '{namespace}:{name}' created successfully."}

def delete_article_s(namespace: str, name: str, deletedBy: str):
    json_path = PAGES_DIR / f"{namespace}/{name}.json"

    if not json_path.exists():
        raise HTTPException(404, f"Article '{namespace}:{name}' not found")
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["deleted"] = True
    data["deletionInfo"] = {
        "user": deletedBy
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return {"status": "success", "message": f"Article '{namespace}:{name}' deleted successfully."}

def return_deletion_status(namespace: str, name: str):
    json_path = PAGES_DIR / f"{namespace}/{name}.json"

    if not json_path.exists():
        raise HTTPException(404, f"Article '{namespace}:{name}' not found")
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {"status": data.get("deleted", False)}

def restore_article_s(namespace: str, name: str):
    json_path = PAGES_DIR / f"{namespace}/{name}.json"

    if not json_path.exists():
        raise HTTPException(404, f"Article '{namespace}:{name}' not found")
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["deleted"] = False

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return {"status": "success", "message": f"Article '{namespace}:{name}' restored successfully."}

def protect_article_s(namespace: str, name: str, protected: str):
    json_path = PAGES_DIR / f"{namespace}/{name}.json"

    if not json_path.exists():
        raise HTTPException(404, f"Article '{namespace}:{name}' not found")
    
    protection_states = ["none", "semiprotected", "protected", "superprotected"]

    if not protected in protection_states:
        raise HTTPException(status_code=422, detail="Invalid protection state")
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["protected"] = protected

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return {"status": "success", "message": f"Article '{namespace}:{name}' protected successfully."}

def return_protection_status(namespace: str, name: str):
    json_path = PAGES_DIR / f"{namespace}/{name}.json"

    if not json_path.exists():
        raise HTTPException(404, f"Article '{namespace}:{name}' not found")
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {"status": data.get("protected", "none")}

def move_article_s(ns: str, name: str, newNS: str, newName: str, createRedirection: bool):
    md_path = PAGES_DIR / f"{ns}/{name}.md"
    json_path = PAGES_DIR / f"{ns}/{name}.json"
    ns_path = PAGES_DIR / ns

    # check ns
    if not os.path.isdir(ns_path):
        raise HTTPException(status_code=400, detail="Wrong namespace")

    if not md_path.exists():
        raise HTTPException(status_code=404, detail="Page not found")
    
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Page not found")
    
    data = return_article(ns, name, True)
    content = data.get("content", "")
    title = data.get("title", "")
    
    if createRedirection == True:
        save_article(ns, name, f"$$REDIRECT:{newNS}:{newName}$$")
    
    success = create_article_s(newNS, newName, title, content, False)
    if not success.get("error", None) == None:
        save_article(ns, name, content)
        return {"error": f"{success.get("error", "")} while creating {newNS}:{newName}"}
    
    return {"status": "success", "message": f"Article '{ns}:{name}' moved successfully into '{newNS}:{newName}'."}