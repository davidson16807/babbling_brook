"""Edit a P3 level: python editor.py data/world.ppm."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent

# Run the checkout directly, as the standalone highlight demo does.
if 'babbling_brook' not in sys.modules:
    spec = spec_from_file_location(
        'babbling_brook', ROOT / 'code' / '__init__.py',
        submodule_search_locations=[str(ROOT / 'code')],
    )
    package = module_from_spec(spec)
    sys.modules['babbling_brook'] = package
    spec.loader.exec_module(package)

from babbling_brook.editor.editor import main


if __name__ == '__main__':
    main()
