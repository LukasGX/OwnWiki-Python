import markdown
import re

def get_html(md: str):
    html = markdown.markdown(md)

    # Templates
    def repl(match):
        mention = match.group(1).replace("%", " ")
        splitted = mention.split(":")

        try:
            from services.article_service import return_article
            template = return_article("template", splitted[0])
            content = template["content"]

            def repll(match):
                arg = match.group(1)

                try:
                    return splitted[int(arg)]
                except:
                    return ""

            pattern = r'##(\d+)'
            content = re.sub(pattern, repll, content)
            return content
        except:
            pass

    pattern = r'(?<!\\)@([a-zA-Z0-9_:%]+)'
    html = re.sub(pattern, repl, html)

    pattern = r'\\@([a-zA-Z0-9_:%]+)'
    html = re.sub(pattern, r'@\1', html)

    return html