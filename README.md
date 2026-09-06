# Babbling Brook

This revision implements the model and codec foundation from the supplied source.
The original rendering sketches remain under `code/view/`; the application loop,
views, simulation systems, and updaters are still to be implemented. There is no
playable desktop application in this revision.

The original `code/` source layout is preserved. Packaging exposes it as
`babbling_brook`, avoiding clashes with Python's built-in `code` and `codecs`
modules.

## Install and verify

Requires Python 3.10 or later. From this directory:

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
```

The model and codecs require only PyGLM. Installing the optional `render` extra
also enables the two Pygame event-adapter checks:

```sh
python -m pip install -e '.[render]'
```

