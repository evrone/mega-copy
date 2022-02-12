import sys
from fs_utils import _run, read_file
from termcolor import cprint, colored
import glob
import libcst



print("hello", sys.argv)


if __name__ == "__main__":
    a = _run(r'git status --porcelain', 3)
    if len(a[1]):
        cprint("Error: Git isn\'t clean, can\'t perform work\n", "red")
        sys.exit(1)
    files = glob.glob("**/*.py")
    terms = sys.argv[1:-1]
    replace = sys.argv[-1]
    print(f"Will try replace {', '.join(terms)} by {replace} in files above")
    for filename in files:
        print("Reading", colored(filename, "green"))
        f = libcst.parse_module(read_file(filename))
