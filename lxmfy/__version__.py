from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
import tomllib

try:
    __version__ = version("lxmfy")
except PackageNotFoundError:
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)
    __version__ = pyproject["project"]["version"]
