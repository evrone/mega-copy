import sys
from fs_utils import _run
from termcolor import cprint


print("hello", sys.argv)


if __name__ == "__main__":
    a = _run(r'git status --porcelain', 3)
    if len(a[1]):
        cprint("Error: Git isn\'t clean, can\'t perform work\n", "red")
        sys.exit(1)
