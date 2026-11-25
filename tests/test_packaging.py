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


def test_readme_has_no_unfinished_markers():
    readme = (PYPROJECT.parent / "README.md").read_text(encoding="utf-8").lower()
    for marker in ("in development", "planned", "<repo-url>"):
        assert marker not in readme


def test_readme_documents_the_data_file():
    readme = (PYPROJECT.parent / "README.md").read_text(encoding="utf-8")
    assert "data.pkl" in readme
    assert ".bak" in readme


def test_authors_are_listed_with_full_names(project):
    readme = (PYPROJECT.parent / "README.md").read_text(encoding="utf-8")
    for author in project["authors"]:
        assert f"- {author['name']}" in readme


def test_every_command_is_in_the_readme_usage_tables():
    from personal_assistant.cli import Command

    readme = (PYPROJECT.parent / "README.md").read_text(encoding="utf-8")
    usage = readme.split("## Usage")[1].split("## Project structure")[0]
    for command in Command:
        assert f"`{command.keyword}" in usage, command.keyword


def test_readme_usage_follows_the_help_groups():
    from personal_assistant.cli import Command

    readme = (PYPROJECT.parent / "README.md").read_text(encoding="utf-8")
    usage = readme.split("## Usage")[1].split("## Project structure")[0]
    titles = {
        "Contacts": "Contact commands",
        "Notes": "Note commands",
        "General": "General commands",
    }
    sections = {
        group: usage.split(f"### {title}")[1].split("###")[0]
        for group, title in titles.items()
    }
    for command in Command:
        assert f"`{command.keyword}" in sections[command.group], command.keyword


def test_readme_usage_rows_follow_the_command_order():
    import re

    from personal_assistant.cli import Command

    index = {command.keyword: i for i, command in enumerate(Command)}
    readme = (PYPROJECT.parent / "README.md").read_text(encoding="utf-8")
    usage = readme.split("## Usage")[1].split("## Project structure")[0]
    for title in ("Contact commands", "Note commands", "General commands"):
        section = usage.split(f"### {title}")[1].split("###")[0]
        positions = [
            index[re.search(r"`([a-z-]+)", row).group(1)]
            for row in section.splitlines()
            if row.startswith("| `")
        ]
        assert positions == sorted(positions), title
