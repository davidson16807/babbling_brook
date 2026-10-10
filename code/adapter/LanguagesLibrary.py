"""Import the languages repo (github.com/davidson16807/languages) as a library.

Its `language-learning` folder holds two top-level packages, `tools` and
`languages`. Their modules read their tables relative to the working directory
while they are imported, so imports happen here, once, with that folder as the
working directory; the previous one is restored afterwards. After that, the
imported modules need neither the folder nor the working directory: `Language.map`
and the dictstores read no files.

The `inflections_for_*.py` scripts write flashcard decks when imported, so they
are not imported; game modules play their part instead (see `lexicon/`).
"""
import importlib
import os
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class LanguagesLibrary:
    ENVIRONMENT = 'BB_LANGUAGES'
    CANDIDATES = (
        ROOT / 'lib' / 'languages' / 'language-learning',  # git submodule
        ROOT.parent / 'languages' / 'language-learning',   # sibling checkout
    )

    def __init__(self, directory=None):
        """`directory` is the repo's language-learning folder, or the repo itself."""
        candidates = ([Path(directory)] if directory is not None
                      else [Path(os.environ[self.ENVIRONMENT])] if self.ENVIRONMENT in os.environ
                      else self.CANDIDATES)
        for candidate in candidates:
            for folder in (candidate, candidate / 'language-learning'):
                if (folder / 'tools' / 'dictstores.py').is_file():
                    self.directory = folder.resolve()
                    return
        raise FileNotFoundError(
            'Cannot find the languages repo. Run `git submodule update --init`, '
            f'set {self.ENVIRONMENT}, or pass its path; looked in: '
            + ', '.join(str(candidate) for candidate in candidates))

    def import_module(self, name: str):
        """Import a library module, or a game module that imports library modules."""
        for package in ('tools', 'languages'):
            loaded = sys.modules.get(package)
            paths = [Path(path).resolve() for path in getattr(loaded, '__path__', [])]
            if loaded is not None and self.directory / package not in paths:
                raise ImportError(f'A different `{package}` module is already imported: {loaded!r}')
        if str(self.directory) not in sys.path:
            sys.path.insert(0, str(self.directory))
        previous = os.getcwd()
        os.chdir(self.directory)
        try:
            with warnings.catch_warnings():
                # Regex strings in the library predate Python 3.12's invalid-escape warnings.
                warnings.simplefilter('ignore', SyntaxWarning)
                return importlib.import_module(name)
        finally:
            os.chdir(previous)
