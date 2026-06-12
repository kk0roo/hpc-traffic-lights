import json
import os


def ensure_dir(path):
    if not path:
        return
    head, tail = os.path.split(path)
    if os.path.splitext(tail)[1]:
        directory = head
    else:
        directory = path
    if directory:
        os.makedirs(directory, exist_ok=True)


def load_json(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(data, path):
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=False)
        handle.write("\n")
