"""Smoke tests: is the environment set up correctly?

These run first and fastest. If any of them fail, every other test result is
meaningless, because we'd be testing against the wrong Python or the wrong
library versions.
"""

import importlib
import importlib.metadata
from pathlib import Path

import pytest

# requirements-tx2.txt sits in the repo root, one level above tests/.
REPO_ROOT = Path(__file__).resolve().parents[1]
PINNED_FILE = REPO_ROOT / "requirements-tx2.txt"


def read_pins(path: Path) -> list[tuple[str, str]]:
    """Return [(distribution_name, version), ...] from a pinned requirements file.

    Blank lines and comments are skipped. Every other line must be an exact
    pin ("name==version"); anything else raises ValueError, because an
    unpinned line would defeat the point of the file.
    """
    pins = []
    for line_number, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if "==" not in line:
            raise ValueError(f"{path.name}:{line_number}: not an exact pin: {raw!r}")
        name, version = (part.strip() for part in line.split("==", 1))
        pins.append((name, version))
    return pins


PINS = read_pins(PINNED_FILE)


def test_package_imports():
    """Our own package is installed and importable."""
    import walle_planner

    assert walle_planner.__name__ == "walle_planner"


def test_pinned_file_is_not_empty():
    """Guards against an empty requirements file making the next test vacuous."""
    assert PINS, f"{PINNED_FILE.name} has no pinned packages"


@pytest.mark.parametrize(("name", "pinned"), PINS, ids=[name for name, _ in PINS])
def test_installed_version_matches_pin(name, pinned):
    """Each package is installed at exactly the version we verified on the TX2."""
    installed = importlib.metadata.version(name)
    assert installed == pinned, f"{name}: installed {installed}, pinned {pinned}"


# Import names differ from install names for two of these:
# PyYAML is imported as "yaml", pyserial as "serial".
@pytest.mark.parametrize("module", ["numpy", "scipy", "numba", "yaml", "serial"])
def test_runtime_dependency_imports(module):
    """Installed isn't enough: the compiled parts must actually load."""
    importlib.import_module(module)