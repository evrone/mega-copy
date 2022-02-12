import sys
from fs_utils import _run


print("hello", sys.argv)

a=_run(r'git status --porcelain', 3)
print(a[0], a[1], len(a[1]))

