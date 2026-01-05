import json
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent

def get_rights_by_role(role: str):
    with (ROOT_DIR / "static" / "rights.json").open("r", encoding="utf-8") as f:
        rights_data = json.load(f)
    return rights_data.get(role, {"read": True, "createaccount": True})