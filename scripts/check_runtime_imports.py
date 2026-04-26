from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

THIRD_PARTY_MODULES = [
    "anthropic",
    "bcrypt",
    "dotenv",
    "fastapi",
    "flask",
    "flask_cors",
    "joblib",
    "jose",
    "jwt",
    "matplotlib.pyplot",
    "numpy",
    "openpyxl",
    "pandas",
    "plotly.express",
    "plotly.graph_objects",
    "pydantic",
    "redis",
    "reportlab",
    "requests",
    "schedule",
    "sklearn",
    "sqlalchemy",
    "streamlit",
    "uvicorn",
    "xlsxwriter",
]

APP_MODULES = [
    "ai_integration",
    "core_modules.analytics",
    "core_modules.auth",
    "core_modules.config",
    "core_modules.database",
    "core_modules.email_service",
    "enhancements.ml_engine",
    "enhancements.report_generator",
    "ui_pages.ai_page",
    "ui_pages.reports_page",
    "ui_pages.risk_page",
    "ui_pages.settings_page",
]

ENTRY_FILES = [
    ROOT / "app.py",
    ROOT / "run_api.py",
]


def import_file_module(path: Path) -> None:
    spec = importlib.util.spec_from_file_location(f"smoke_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


def main() -> int:
    failures: list[str] = []
    for module_name in THIRD_PARTY_MODULES + APP_MODULES:
        try:
            importlib.import_module(module_name)
            print(f"[OK] {module_name}")
        except Exception as exc:
            failures.append(f"{module_name}: {exc}")
            print(f"[FAIL] {module_name}: {exc}")

    for path in ENTRY_FILES:
        try:
            import_file_module(path)
            print(f"[OK] {path.name}")
        except Exception as exc:
            failures.append(f"{path.name}: {exc}")
            print(f"[FAIL] {path.name}: {exc}")

    if failures:
        print("\nImport smoke check failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("\nAll runtime imports succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
