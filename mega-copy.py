import re
import json
from pygments import highlight, lexers, formatters
import sys
from fs_utils import _run, read_file, write_file
from parser_utils import serialize_dc, unserialize_dc
from termcolor import cprint, colored
import glob
import libcst
from collections import defaultdict


def jprint(d):
    formatted_json = json.dumps(d, indent=4, default=repr)
    colorful_json = highlight(
        formatted_json, lexers.JsonLexer(), formatters.TerminalFormatter()
    )
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


def walktree(node, f, path=None):
    if path is None:
        path = []
    t = type(node)
    if t == dict:
        result = {}
        for k, v in node.items():
            result[k] = walktree(v, f, path + [(k, node.get("type"))])
        return result
    elif t in [list, tuple, set]:
        result = []
        for i, x in enumerate(node):
            result.append(walktree(x, f, path + [(i, str(t))]))
        return t(result)
    else:
        return f(node, path)


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
    print("The regexp", regexp)
    if action == "list":
        data = defaultdict(int)

        def f(node, *args, **kwargs):
            if type(node) == str:
                for s in re.findall(regexp, node, re.I):
                    print(s)
                    data[s] += 1
            return node

        for filename in files:
            print("Reading", colored(filename, "green"))
            m = libcst.parse_module(read_file(filename))
            serialized = serialize_dc(m)
            walktree(serialized, f)
        jprint(data)
    if action == "list_paths":
        data = defaultdict(int)

        def f(node, path):
            if type(node) == str:
                for s in re.findall(regexp, node, re.I):
                    print(path)
                    data[s] += 1
            return node

        for filename in files:
            print("Reading", colored(filename, "green"))
            m = libcst.parse_module(read_file(filename))
            serialized = serialize_dc(m)
            walktree(serialized, f)
        jprint(data)
    if action == "copy":

        def f(node, path):
            if type(node) == str:
                for s in re.findall(regexp, node, re.I):
                    paths.add(tuple(path))
            return node

        for filename in files:
            paths = set([])
            print("Reading", colored(filename, "green"))
            code = read_file(filename)
            m = libcst.parse_module(code)
            tree = serialize_dc(m)
            walktree(tree, f)
            correct_paths = set([])

            def is_correct_position(path, i):
                try:
                    v1, t1 = path[-1 * (i + 1)]
                    v2, t2 = path[-1 * (i + 1) - 1]
                except IndexError:
                    return False
                print(t1, t2)
                if t1 == "<class 'list'>" and t2 in ["Module", "Dict"]:
                    return True

            for path in paths:
                for i in range(len(path) - 1):
                    if is_correct_position(path, i):
                        correct_paths.add(tuple([x[0] for x in path]))
                        break
            correct_paths = sorted(correct_paths, key=len)
            jprint(correct_paths)
            new_tree = walktree(tree, lambda n, p: n)
            u = unserialize_dc(new_tree)
            if len(u.code) == len(code):
                cprint("Yes", "grey")
            else:
                cprint("No", "yellow")
            # write_file(filename, u.code)
