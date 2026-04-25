from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


def _load_legacy_app_module():
    module_name = "_vendor_insight_legacy_app"
    if module_name in sys.modules:
        return sys.modules[module_name]

    legacy_app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = spec_from_file_location(module_name, legacy_app_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load legacy app module from {legacy_app_path}")

    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def __getattr__(name):
    if name == "VendorDashboard":
        return getattr(_load_legacy_app_module(), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["VendorDashboard"]
