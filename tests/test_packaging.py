"""The package metadata the course requires: an installable console command."""

import importlib
from pathlib import Path

import pytest

tomllib = pytest.importorskip("tomllib")  # Python 3.11+

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


@pytest.fixture(scope="module")
def project() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]


def test_console_script_points_to_a_real_function(project):
    module_name, _, function_name = project["scripts"]["assistant"].partition(":")
    function = getattr(importlib.import_module(module_name), function_name)
    assert callable(function)


def test_python_version_matches_the_readme(project):
    readme = (PYPROJECT.parent / "README.md").read_text(encoding="utf-8")
    minimum = project["requires-python"].removeprefix(">=")
    assert f"Python {minimum}+" in readme


def test_readme_is_the_package_readme(project):
    assert project["readme"] == "README.md"
    assert (PYPROJECT.parent / "README.md").is_file()
