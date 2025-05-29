import subprocess
import os

PACKAGES = ["qwen_api", "qwen_llamaindex"]

def has_changes(package):
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main", "HEAD", "--", package],
        capture_output=True, text=True
    )
    return bool(result.stdout.strip())

changed = [pkg for pkg in PACKAGES if has_changes(pkg)]

# Print sebagai matrix YAML
if changed:
    print("::set-output name=matrix::{\"include\": " + str([{"package": p} for p in changed]) + "}")
else:
    print("::set-output name=matrix::{\"include\": []}")
