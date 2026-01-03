def get_role_color(role: str):
    role_colors = {
        "admin": "#FFC8C8",
        "interface-admin": "#FFC8C8",
        "bureaucrat": "#FFC8C8",
        "oversighter": "#FFC8C8",
        "bot": "#C3C3FF"
    }
    return role_colors.get(role, "rgba(0, 0, 0, 0.1)")