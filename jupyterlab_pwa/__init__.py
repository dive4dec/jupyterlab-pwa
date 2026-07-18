"""Server extension: PWA support for JupyterLab."""

from ._version import __version__  # noqa: F401


def _jupyter_server_extension_points():
    return [{"module": "jupyterlab_pwa"}]


def _load_jupyter_server_extension(serverapp):
    """Load hook for Jupyter Server 2.x."""
    from .handlers import _setup_pwa

    _setup_pwa(serverapp)


# Backward-compatible alias
load_jupyter_server_extension = _load_jupyter_server_extension


def _jupyter_labextension_paths():
    return []
