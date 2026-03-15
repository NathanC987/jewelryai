from __future__ import annotations

import json
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.component_catalog import component_catalog


def main() -> None:
    summary = component_catalog.audit()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
