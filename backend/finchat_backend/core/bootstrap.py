"""Backend bootstrap helpers."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
# Add the directory that contains the agent_service package to sys.path
# That directory is backend/finchat_backend
FINCHAT_BACKEND_DIR = ROOT_DIR / "backend" / "finchat_backend"


def ensure_project_path() -> None:
    """Ensure agent_service modules are importable."""
    backend_path = str(FINCHAT_BACKEND_DIR)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)


ensure_project_path()
