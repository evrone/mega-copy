import os
import re
import copy
import sys
import glob
import libcst
from termcolor import cprint, colored
from collections import defaultdict

from fs_utils import _run, read_file, write_file
from parser_utils import serialize_dc, unserialize_dc
from print_utils import jprint


def generate_variants(source, replacement):
    # property sale
    # property-sale
    # property_sale
    # PropertySale
    # Property Sale
    # PROPERTY_SALE
    pass


def get_by_path(tree, path):
    result = tree
    for p in path:
        result = result[p]
    return result


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


def copy_at_paths(tree, paths_to_visit, replace_fn):
    def walktree2(node, c, path=None):
        if path is None:
            path = []
        t = type(node)
        if t == dict:
            result = {}
            for k, v in node.items():
                result[k] = walktree2(v, c, path + [(k, node.get("type"))])
            return result
        elif t in [list, tuple, set]:
            result = []
            for i, x in enumerate(node):
                element_path = path + [(i, str(t))]
                content = c(walktree2(x, c, element_path), element_path)
                result.extend(content)
            return t(result)
        else:
            return node

    def c(node, path):
        path2 = [p[0] for p in path]
        if path2 in paths_to_visit:
            # jprint(node)
            # jprint(walktree(copy.deepcopy(node), replace_fn))
            # raise
            return [node, walktree(copy.deepcopy(node), replace_fn)]
        else:
            return [node]

    return walktree2(tree, c)


def get_spellings(term):
    options = []
    lower = [p.lower() for p in term.replace("_", "-").split("-")]
    upper = [p.upper() for p in lower]
    capitalize = [p.capitalize() for p in lower]
    capitalize_first = [capitalize[0]] + lower[1:]
    capitalize_rest = [lower[0]] + capitalize[1:]
    for cased in [
        lower,
        upper,
        capitalize,
        capitalize_first,
        capitalize_rest,  # camelCase ?
    ]:
        for joint in ["", " ", "-", "_"]:
            options.append(joint.join(cased))
    return options


def make_replace_fn(regexp, terms, replace):
    replace_map = {}
    if terms and len(terms[0].split("-")) > 1:
        replace_spellings = get_spellings(replace)
        for term in terms:
            replace_map.update(
                dict(map(lambda a, b: [a, b], get_spellings(term), replace_spellings))
            )
    else:
        t = terms[0]
        r = replace.split("-")
        replace_map = {
            t.lower(): "_".join([w.lower() for w in r]),
            t.lower().capitalize(): "".join([w.lower().capitalize() for w in r]),
            t.upper(): "_".join([w.upper() for w in r]),
        }
    print("Replace map")
    jprint(replace_map)

    def replace_fn(value, *args, **kwargs):
        if type(value) != str:
            return value

        def repl(matchobj):
            return replace_map[matchobj.group()]

        return re.sub(regexp, repl, value)

    return replace_fn


def make_mark_fn(regexp):
    def mark_fn(value, *args, **kwargs):
        if type(value) != str:
            return value

        def repl(matchobj):
            return colored(matchobj.group(), "magenta", attrs=["bold"])

        return re.sub(regexp, repl, value)

    return mark_fn


results = []

if __name__ == "__main__":
    action = sys.argv[1]
    if "show" not in action:
        a = _run(r"git status --porcelain", 3)
        if len(a[1]):
            cprint("Error: Git isn't clean, can't perform work\n", "red")
            sys.exit(1)
    files = glob.glob("**/*.py", recursive=True)
    subaction = None
    if "-" in action:
        action, subaction = action.split("-")
    file_arg = None
    if (action == "file") or subaction == "file":  # has filename arg in the end
        terms = sys.argv[2:-2]
        replace = sys.argv[-2]
        file_arg = sys.argv[-1]
    else:
        terms = sys.argv[2:-1]
        replace = sys.argv[-1]
    print(f"Will try replace {', '.join(terms)} by {replace} in files above")
    data = None
    variants = []
    for v in terms:
        parts = [re.escape(p) for p in v.split("-")]
        variants.append(r"[ \-\_]?".join(parts))
    regexp = f"({'|'.join(variants)})"
    result_parts = [re.escape(p) for p in replace.split("-")]
    result_regexp = r"[ \-\_]?".join(result_parts)
    regexp = re.compile(regexp, flags=re.I)
    # fns
    replace_fn = make_replace_fn(regexp, terms, replace)
    mark_fn = make_mark_fn(re.compile(result_regexp, flags=re.I))
    print("The regexp", regexp)
    if action == "list":
        data = defaultdict(int)

        def f(node, *args, **kwargs):
            if type(node) == str:
                for s in re.findall(regexp, node):
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
                for s in re.findall(regexp, node):
                    print(path)
                    data[s] += 1
            return node

        for filename in files:
            print("Reading", colored(filename, "green"))
            m = libcst.parse_module(read_file(filename))
            serialized = serialize_dc(m)
            walktree(serialized, f)
        jprint(data)
    if action == "pycopy":

        def f(node, path):
            if type(node) == str:
                for s in re.findall(regexp, node):
                    paths.add(tuple(path))
            return node

        for filename in files:
            if "/node_modules/" in filename:
                continue
            if "/migrations/" in filename:
                continue
            if "/venv/" in filename:
                continue
            if "/.venv/" in filename:
                continue
            if filename.startswith("venv/") or filename.startswith(".venv/"):
                continue
            paths = set([])
            print("Reading", colored(filename, "green"))
            code = read_file(filename)
            m = libcst.parse_module(code)
            tree = serialize_dc(m)
            walktree(tree, f)
            correct_paths = set([])
            incorrect_paths = []  # perserve order

            def is_correct_position(path, i):
                try:
                    v1, t1 = path[-1 * (i + 1)]
                    v2, t2 = path[-1 * (i + 1) - 1]
                except IndexError:
                    return False
                # print(t1, t2)
                if t2 in ["ClassDef"] and t1 == "Name":
                    return True

            for path in paths:
                is_correct = False
                for i in range(len(path) - 1):
                    if is_correct_position(path, i):
                        correct_paths.add(tuple([x[0] for x in path[: -i - 2]]))
                        is_correct = True
                        break
                    else:
                        path2 = path[:2]
                        if path2 not in incorrect_paths:
                            incorrect_paths.append(path2)
            correct_paths = sorted([list(p) for p in correct_paths], key=len)
            for i in range(len(correct_paths)):
                for j in range(i + 1, len(correct_paths)):
                    if all(
                        map(
                            lambda a, b: a == b,
                            correct_paths[i],
                            correct_paths[j][: len(correct_paths[i])],
                        )
                    ):
                        print("Eliminate")
            # jprint(correct_paths)
            if correct_paths:
                new_tree = copy_at_paths(tree, correct_paths, replace_fn)
                u = unserialize_dc(new_tree)
                if len(u.code) == len(code):
                    cprint("The same", "grey")
                else:
                    cprint("Different", "yellow")
                    write_file(filename, u.code)
            if incorrect_paths:
                for path in incorrect_paths:
                    path = [p[0] for p in path]
                    if path in correct_paths:
                        continue
                    # cprint(path, "red")
                    path_tree = get_by_path(tree, path)
                    path_tree = walktree(path_tree, replace_fn)
                    cprint(path_tree["type"], "red")
                    print(mark_fn(unserialize_dc({**tree, "body": [path_tree]}).code))
    if action == "pyren":

        def f(node, path):
            if type(node) == str:
                for s in re.findall(regexp, node):
                    paths.add(tuple(path))
            return node

        if subaction == "file":
            files = [file_arg]

        for filename in files:
            if "/node_modules/" in filename:
                continue
            if "/migrations/" in filename:
                continue
            if "/venv/" in filename:
                continue
            if "/.venv/" in filename:
                continue
            if filename.startswith("venv/") or filename.startswith(".venv/"):
                continue
            paths = set([])
            print("Reading", colored(filename, "green"))
            code = read_file(filename)
            m = libcst.parse_module(code)
            tree = serialize_dc(m)

            new_tree = walktree(tree, replace_fn)
            u = unserialize_dc(new_tree)
            if u.code == code:
                cprint("The same", "grey")
            else:
                cprint("Different", "yellow")
                write_file(filename, u.code)
    if action == "pyshow":

        def f(node, path):
            if type(node) == str:
                for s in re.findall(regexp, node):
                    paths.add(tuple(path))
            return node

        if subaction == "file":
            files = [file_arg]

        for filename in files:
            if "/node_modules/" in filename:
                continue
            if "/migrations/" in filename:
                continue
            if "/venv/" in filename:
                continue
            if "/.venv/" in filename:
                continue
            if filename.startswith("venv/") or filename.startswith(".venv/"):
                continue
            paths = set([])
            print("Reading", colored(filename, "green"))
            code = read_file(filename)
            m = libcst.parse_module(code)
            tree = serialize_dc(m)

            make_tree = lambda body: {**tree, "body": body}
            new_tree = make_tree([])
            changed = False
            for item in tree["body"]:
                new_item = walktree(item, replace_fn)
                if (
                    unserialize_dc(make_tree([item])).code
                    != unserialize_dc(make_tree([new_item])).code
                ):
                    new_tree["body"].append(new_item)
                    changed = True
            if not changed:
                cprint("The same", "grey")
            else:
                cprint("Different", "yellow")
                u = unserialize_dc(new_tree)
                print(mark_fn(u.code))
    if action == "text" and subaction == "copy":
        if os.path.isfile(file_arg):
            files = [file_arg]
        elif os.path.isdir(file_arg):
            os.chdir(file_arg)
            files = glob.glob("**/*", recursive=True)
        else:
            raise NotImplementedError()
        for file in files:
            if "node_modules/" in file:
                continue
            if os.path.is_dir(file):
                continue
            replaced = replace_fn(
                file
            )  # TODO: check if it's a _dir_ that has a pattern
            try:
                code = read_file(file)
            except Exception as e:
                print("Can't read", colored(file, "yellow"))
                continue
            new_code = replace_fn(code)
            if replaced != file:  # filename itself contains characters
                print("Copying", colored(file, "blue"))
                write_file(replaced, new_code)
            else:
                if new_code != code:
                    print(colored("Reading", "red"), colored(file, "green"))
                    print(mark_fn(new_code))
                else:
                    print("Skipping", colored(file, "grey"))
            # print(mark_fn(replace_fn(code)))
    if action == "file" and subaction == "ren":
        if os.path.isfile(file_arg):
            files = [file_arg]
        elif os.path.isdir(file_arg):
            os.chdir(file_arg)
            files = glob.glob("**/*", recursive=True)
        else:
            raise NotImplementedError()
        for file in files:
            if "node_modules/" in file:
                continue
            if os.path.isdir(file):
                continue
            if file.lower().endswith(".py"):
                continue
            replaced = replace_fn(file)  # TODO: rename the file also? the dirs etc?
            try:
                code = read_file(file)
            except Exception as e:
                print("Can't read", colored(file, "yellow"))
                continue
            new_code = replace_fn(code)
            if new_code != code:
                print("Updating", colored(file, "blue"))
                write_file(replaced, new_code)
            else:
                print("Skipping", colored(file, "grey"))
    if action in ["file", "files"] and subaction == "show":
        if action == "file":
            if os.path.isfile(file_arg):
                files = [file_arg]
            elif os.path.isdir(file_arg):
                os.chdir(file_arg)
                files = glob.glob("**/*", recursive=True)
            else:
                raise NotImplementedError()
        for file in files:
            if "node_modules/" in file:
                continue
            if os.path.isdir(file):
                continue
            if file.lower().endswith(".py"):
                continue
            replaced = replace_fn(file)  # TODO: rename the file also? the dirs etc?
            try:
                code = read_file(file)
            except Exception as e:
                print("Can't read", colored(file, "yellow"))
                continue
            new_code = replace_fn(code)
            if new_code != code:
                print("Updating", colored(file, "blue"))
                print(mark_fn(new_code))
            else:
                print("Skipping", colored(file, "grey"))
