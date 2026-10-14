from importlib.metadata import version

__version__ = "N/A"
try:
    __version__ = version("pitopd")
except Exception:
    pass
