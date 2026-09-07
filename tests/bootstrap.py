"""Allow tests from the source ZIP as well as from an editable installation."""
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if importlib.util.find_spec('babbling_brook') is None:
    spec = importlib.util.spec_from_file_location('babbling_brook', ROOT / 'code' / '__init__.py',
        submodule_search_locations=[str(ROOT / 'code')])
    module = importlib.util.module_from_spec(spec)
    sys.modules['babbling_brook'] = module
    spec.loader.exec_module(module)
