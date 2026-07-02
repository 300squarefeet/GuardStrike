from pathlib import Path

from guardstrike.utils.helpers import (
    list_session_ids,
    resolve_reports_dir,
    resolve_session_path,
)


def test_resolve_reports_dir_from_config():
    assert resolve_reports_dir({"output": {"save_path": "/tmp/x"}}) == Path("/tmp/x")


def test_resolve_reports_dir_defaults():
    assert resolve_reports_dir({}) == Path("./reports")
    assert resolve_reports_dir({"output": {"save_path": None}}) == Path("./reports")
    assert resolve_reports_dir({"output": None}) == Path("./reports")


def test_resolve_session_path():
    p = resolve_session_path({"output": {"save_path": "/tmp/x"}}, "abc")
    assert p == Path("/tmp/x/session_abc.json")


def test_list_session_ids(tmp_path):
    (tmp_path / "session_a.json").write_text("{}")
    (tmp_path / "session_b.json").write_text("{}")
    (tmp_path / "report_a.md").write_text("x")  # ignored
    ids = list_session_ids({"output": {"save_path": str(tmp_path)}})
    assert ids == ["a", "b"]


def test_list_session_ids_missing_dir():
    assert list_session_ids({"output": {"save_path": "/nonexistent/xyz"}}) == []
