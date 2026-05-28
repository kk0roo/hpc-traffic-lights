"""Pytest configuration: make the ``src/`` package importable in tests.

This lets test modules do e.g. ``from simulators.python_simulator import ...``
exactly like the scripts do when run as ``python src/script.py``.
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
