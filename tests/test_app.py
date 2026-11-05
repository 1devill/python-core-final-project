"""End-to-end runs of the real app in a temporary home folder."""

import os
import subprocess
import sys

import pytest

from conftest import SRC_DIR

DATA_FOLDER = ".personal_assistant"


@pytest.mark.parametrize("word", ["exit", "close", "bye", "quit", "EXIT"])
def test_exit_words(app, word):
    result = app(word, end_with_exit=False)
    assert result.returncode == 0
    assert "Goodbye" in result.stdout


def test_end_of_input_exits_and_saves(app):
    result = app("add anna 0123456789", end_with_exit=False)
    assert result.returncode == 0
    assert "Anna" in app("all").stdout


def test_data_survives_a_restart(app):
    app(
        "add anna 0123456789",
        "add-birthday anna 29.02.2000",
        "add-email anna a@b.co",
        "add-address anna Kyiv Main St",
        "add-note shop home,food buy milk",
    )
    result = app("all", "all-notes", "find-contacts address=kyiv")
    assert result.returncode == 0
    for expected in ("29.02.2000", "a@b.co", "Kyiv Main St", "#food", "buy milk", "Found contacts (1)"):
        assert expected in result.stdout


def test_removed_data_stays_removed(app):
    app("add anna 0123456789", "add-note shop home milk")
    app("remove anna", "remove-note shop")
    result = app("all", "all-notes")
    assert "No contacts yet." in result.stdout
    assert "No notes yet." in result.stdout


def test_empty_and_unknown_lines_keep_the_loop_running(app):
    result = app("", "    ", "nonsense", "find-contact", "hello")
    assert result.returncode == 0
    assert "Unknown command 'nonsense'" in result.stdout
    assert "Did you mean 'find-contacts'?" in result.stdout
    assert "Hello!" in result.stdout


def test_help_lists_new_commands(app):
    result = app("help")
    assert "find-contacts" in result.stdout
    assert "show-upcoming-birthdays" in result.stdout


def test_non_ascii_data(app):
    app("add Олена 0123456789", "add-address Олена Київ, Хрещатик 1")
    result = app("find-contacts address=КИЇВ")
    assert result.returncode == 0
    assert "Found contacts (1)" in result.stdout


def test_corrupted_file_does_not_stop_the_app(app):
    folder = app.home / DATA_FOLDER
    folder.mkdir()
    (folder / "data.pkl").write_bytes(b"broken")
    result = app("add anna 0123456789", "all")
    assert result.returncode == 0
    assert "corrupted" in result.stdout
    assert "Anna" in result.stdout


@pytest.mark.xfail(strict=True, reason="BUG: a failed save on exit ends in a traceback")
def test_failed_save_on_exit_does_not_crash(app):
    (app.home / DATA_FOLDER).write_text("a file where the folder should be")
    result = app("add anna 0123456789")
    assert result.returncode == 0
    assert "Traceback" not in result.stderr


@pytest.mark.xfail(strict=True, reason="BUG: data is saved only on exit, a killed app loses it")
@pytest.mark.skipif(sys.platform == "win32", reason="needs POSIX signals")
def test_killed_app_keeps_finished_commands(app):
    env = {**os.environ, "HOME": str(app.home), "PYTHONPATH": str(SRC_DIR), "PYTHONUNBUFFERED": "1"}
    process = subprocess.Popen(
        [sys.executable, "-m", "personal_assistant"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        env=env,
    )
    process.stdin.write("add anna 0123456789\n")
    process.stdin.flush()
    for line in process.stdout:
        if "added" in line:
            break
    process.terminate()
    process.wait(timeout=10)
    process.stdout.close()
    process.stdin.close()
    assert "Anna" in app("all").stdout
