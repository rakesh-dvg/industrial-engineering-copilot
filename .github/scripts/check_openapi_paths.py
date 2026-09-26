"""Verify Phase 1 OpenAPI paths are registered in the FastAPI application."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.main import create_app  # noqa: E402


def main() -> int:
    contract = yaml.safe_load((ROOT / "openapi.yaml").read_text(encoding="utf-8"))
    contract_paths = set(contract.get("paths", {}).keys())

    app = create_app()
    app_paths = set(app.openapi().get("paths", {}).keys())

    missing = sorted(path for path in contract_paths if path not in app_paths)
    if missing:
        print("OpenAPI paths missing from FastAPI app:")
        for path in missing:
            print(f"  - {path}")
        return 1

    print("OpenAPI Phase 1 path check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
