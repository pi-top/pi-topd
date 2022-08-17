from pkg_resources import get_distribution

__version__ = "N/A"
try:
    __version__ = get_distribution("pitopd").version
except Exception:
    pass
