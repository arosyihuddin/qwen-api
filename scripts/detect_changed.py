import toml
import requests
import json
import os

packages = ["qwen_api", "qwen_llamaindex"]
changed = []

def get_pypi_version(package_name):
    url = f"https://pypi.org/pypi/{package_name}/json"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json()['info']['version']
    return None

for pkg in packages:
    local_version = toml.load(f"{pkg}/pyproject.toml")["project"]["version"]
    pypi_version = get_pypi_version(pkg)
    if pypi_version is None or local_version != pypi_version:
        changed.append({"package": pkg})

matrix = json.dumps({"include": changed})

# Output ke GITHUB_OUTPUT kalau di CI, atau tampilkan di lokal
if "GITHUB_OUTPUT" in os.environ:
    with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
        fh.write(f"matrix={matrix}\n")
else:
    print("Matrix (local run):")
    print(matrix)