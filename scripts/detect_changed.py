import os
import json
import subprocess

# Daftar package di dalam monorepo
packages = ["qwen_api", "qwen_llamaindex"]
changed = []

# Ambil tag terakhir (rilis sebelumnya)
try:
    last_tag = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"], text=True).strip()
except subprocess.CalledProcessError:
    # Kalau belum ada tag, gunakan root awal (semua dianggap berubah)
    last_tag = ""

for package in packages:
    if last_tag:
        diff_range = f"{last_tag}..HEAD"
    else:
        diff_range = "HEAD"

    result = subprocess.run(
        ["git", "diff", "--name-only", diff_range, "--", package],
        capture_output=True, text=True
    )
    if result.stdout.strip():
        changed.append(package)

# Siapkan matrix untuk GitHub Actions
matrix = json.dumps({ "include": [{"package": name} for name in changed] })

# Output ke GITHUB_OUTPUT kalau di CI, atau tampilkan di lokal
if "GITHUB_OUTPUT" in os.environ:
    with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
        fh.write(f"matrix={matrix}\n")
else:
    print("Matrix (local run):")
    print(matrix)