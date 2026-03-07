import os
import json
from fastapi import Request
from services.rights_service import get_rights_by_role

def _pages_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'pages'))

def search_s(request: Request, q: str, namespace: str, page: int, limit: int):
    pages_root = _pages_dir()
    q_norm = (q or '').strip().lower()
    ns_filter = (namespace or '').strip()

    # determine whether the requesting user may browse deleted pages
    user_rights = {}
    roles_raw = request.session.get("roles", ["default"]) or ["default"]
    for role in roles_raw[0].split(";"):
        rights = get_rights_by_role(role)
        for right, value in rights.items():
            user_rights[right] = value
    include_deleted = bool(user_rights.get("browsedeleted", False))

    if limit is None or limit <= 0:
        limit = 10
    if page is None or page < 1:
        page = 1

    files = []
    if ns_filter:
        ns_dir = os.path.join(pages_root, ns_filter)
        if os.path.isdir(ns_dir):
            for fname in os.listdir(ns_dir):
                if fname.endswith('.json') and not fname.endswith('_discussion.json'):
                    files.append((ns_filter, fname[:-5], os.path.join(ns_dir, fname)))
    else:
        if os.path.isdir(pages_root):
            for ns in os.listdir(pages_root):
                ns_dir = os.path.join(pages_root, ns)
                if not os.path.isdir(ns_dir):
                    continue
                for fname in os.listdir(ns_dir):
                    if fname.endswith('.json') and not fname.endswith('_discussion.json'):
                        files.append((ns, fname[:-5], os.path.join(ns_dir, fname)))

    results = []
    for ns, name, fpath in files:
        try:
            with open(fpath, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
        except Exception:
            data = {}

        title = name
        deleted = False
        if isinstance(data, dict):
            title = data.get('title') or name
            deleted = bool(data.get('deleted', False))
        elif isinstance(data, list):
            first_dict = None
            for item in data:
                if isinstance(item, dict):
                    first_dict = item
                    if 'title' in item or 'deleted' in item:
                        break
            if first_dict:
                title = first_dict.get('title') or name
                deleted = bool(first_dict.get('deleted', False))

        # skip deleted pages unless user has the browsedeleted right
        if deleted and not include_deleted:
            continue

        if q_norm:
            if q_norm in title.lower() or q_norm in name.lower():
                results.append({'name': f'{ns}:{name}', 'title': title, 'deleted': deleted})
        else:
            results.append({'name': f'{ns}:{name}', 'title': title, 'deleted': deleted})

    results.sort(key=lambda r: (r['title'] or '').lower())

    start = (page - 1) * limit
    end = start + limit
    paged = results[start:end]

    return {
        "params":{
            "query": q,
            "namespace": namespace,
            "page": page,
            "limit": limit
        },
        "results": paged
    }