import re
import json
from pygments import highlight, lexers, formatters
import sys
from fs_utils import _run, read_file
from parser_utils import serialize_dc
from termcolor import cprint, colored
import glob
import libcst
from collections import defaultdict


def jprint(d):
    formatted_json = json.dumps(d, indent=4, default=repr)
    colorful_json = highlight(formatted_json, lexers.JsonLexer(), formatters.TerminalFormatter())
    print(colorful_json)


print("hello", sys.argv)


def generate_variants(source, replacement):
    # property sale
    # property-sale
    # property_sale
    # PropertySale
    # Property Sale
    # PROPERTY_SALE
    pass


def walktree(node, f):
    if type(node) == dict:
        for k, v in node.items():
            walktree(k, f)
            walktree(v, f)
    elif type(node) in [list, tuple, set]:
        for x in node:
            walktree(x, f)
    else:
        f(node)


results = []

if __name__ == "__main__":
    a = _run(r"git status --porcelain", 3)
    if len(a[1]):
        cprint("Error: Git isn't clean, can't perform work\n", "red")
        sys.exit(1)
    files = glob.glob("**/*.py")
    action = sys.argv[1]
    terms = sys.argv[2:-1]
    replace = sys.argv[-1]
    print(f"Will try replace {', '.join(terms)} by {replace} in files above")
    data = None
    variants = []
    for v in terms:
        parts = [re.escape(p) for p in v.split("-")]
        variants.append(r"[ \-\_]?".join(parts))
    regexp = f"({'|'.join(variants)})"
    re.compile(regexp)
    def f(node):
        if type(node) == str:
            for s in re.findall(regexp, node, re.I):
                print(s)
                data[s] += 1
    print("The regexp", regexp)
    if action == "list":
        data = defaultdict(int)
        for filename in files:
            print("Reading", colored(filename, "green"))
            m = libcst.parse_module(read_file(filename))
            serialized = serialize_dc(m)
            if action == "list":
                walktree(serialized, f)
        jprint(data)
