"""Small, dependency-free I/O helpers used across the project.

Keeping these in one place means every script reads/writes JSON and creates
directories in exactly the same way.
"""

import json
import os


def ensure_dir(path):
    """Create ``path`` (a directory) if it does not already exist.

    Accepts either a directory path or a file path. If ``path`` looks like a
    file path (i.e. it has a non-empty dirname), the parent directory is
    created instead. No error is raised if the directory already exists.
    """
    if not path:
        return
    # If the path has an extension it is most likely a file -> use its parent.
    head, tail = os.path.split(path)
    if os.path.splitext(tail)[1]:
        directory = head
    else:
        directory = path
    if directory:
        os.makedirs(directory, exist_ok=True)


def load_json(path):
    """Load and return the JSON object stored at ``path``.

    Raises FileNotFoundError with a clear message if the file is missing.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(data, path):
    """Serialize ``data`` to ``path`` as pretty-printed JSON.

    The parent directory is created automatically if needed.
    """
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=False)
        handle.write("\n")
