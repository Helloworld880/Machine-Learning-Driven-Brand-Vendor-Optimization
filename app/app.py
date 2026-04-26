from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


def _load_root_streamlit_app():
    module_name = "_vendor_insight_streamlit_root"
    if module_name in sys.modules:
        return sys.modules[module_name]

    root_app_path = Path(__file__).resolve().parents[1] / "app.py"
    spec = spec_from_file_location(module_name, root_app_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load Streamlit app module from {root_app_path}")

    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


main = _load_root_streamlit_app().main


if __name__ == "__main__":
    main()
