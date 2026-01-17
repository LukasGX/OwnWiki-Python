def get_role_color(role: str):
    role_colors = {
        "admin": "#FFC8C8",
        "interface-admin": "#FFC8C8",
        "bureaucrat": "#FFC8C8",
        "oversighter": "#FFC8C8",
        "ownwiki-admin": "#FF8686",
        "bot": "#C3C3FF"
    }
    return role_colors.get(role, "rgba(0, 0, 0, 0.1)")

def get_role_name(role: str):
    role_names = {
        "default": "Standard",
        "user": "Benutzer",
        "autoconfirmed": "Automatisch bestätigt",
        "bot": "Bot",
        "admin": "Administrator",
        "interface-admin": "UI-Administrator",
        "bureaucrat": "Bürokrat",
        "oversighter": "Oversighter",
        "ownwiki-admin": "OwnWiki-Administrator"
    }
    return role_names.get(role, role)