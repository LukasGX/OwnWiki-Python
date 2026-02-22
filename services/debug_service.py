import json
from pathlib import Path
import uuid

ROOT_DIR = Path(__file__).parent.parent

def generate_uuid():
    id = str(uuid.uuid4())
    return {"uuid": id}