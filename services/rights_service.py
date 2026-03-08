import json
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent

def get_rights_by_role(role: str):
    with (ROOT_DIR / "static" / "rights.json").open("r", encoding="utf-8") as f:
        rights_data = json.load(f)
    return rights_data.get(role, {"read": True, "createaccount": True})

def get_rights_s():
    with (ROOT_DIR / "static" / "rights.json").open("r", encoding="utf-8") as f:
        rights_data = json.load(f)

    rights_list = []
    for role, rights in rights_data.items():
        if isinstance(rights, dict):
            for right_name in rights.keys():
                rights_list.append({"right": right_name, "role": role})
        elif isinstance(rights, (list, tuple)):
            for right_name in rights:
                rights_list.append({"right": right_name, "role": role})

    return rights_list