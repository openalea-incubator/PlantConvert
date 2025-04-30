from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("openalea.plantconvert")
except PackageNotFoundError:
    # package is not installed
    pass