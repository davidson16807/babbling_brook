"""Run dialog mode from a checkout: ``python -m dialog``."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
if ((ROOT / 'code' / '__init__.py').is_file()
        and not hasattr(sys.modules.get('babbling_brook'), '__path__')):
    spec = spec_from_file_location(
        'babbling_brook', ROOT / 'code' / '__init__.py',
        submodule_search_locations=[str(ROOT / 'code')],
    )
    package = module_from_spec(spec)
    sys.modules['babbling_brook'] = package
    spec.loader.exec_module(package)

from babbling_brook.dialog.dialog import main


if __name__ == '__main__':
    main()
