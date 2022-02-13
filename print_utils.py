import json
from pygments import highlight, lexers, formatters


def jprint(d):
    formatted_json = json.dumps(d, indent=4, default=repr)
    colorful_json = highlight(
        formatted_json, lexers.JsonLexer(), formatters.TerminalFormatter()
    )
    print(colorful_json)
