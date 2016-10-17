from __future__ import print_function, division
import subprocess
commit = subprocess.check_output(["git", "describe", "--always"])

print(commit)
