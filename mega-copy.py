import sys
from fs_utils import _run


print("hello", sys.argv)

a=_run(r'git status --porcelain', 3)
for i in a[1].splitlines(): print(i)

