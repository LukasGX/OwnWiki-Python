import markdown

def get_html(md: str):
    html = markdown.markdown(md)
    return html