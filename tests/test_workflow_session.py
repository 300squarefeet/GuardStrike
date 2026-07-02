from guardstrike.core.memory import PentestMemory
from guardstrike.core.workflow.session import SessionStore


def test_save_and_resume_roundtrip(tmp_path):
    config = {"output": {"save_path": str(tmp_path)}}
    mem = PentestMemory("example.com")
    sid = mem.session_id
    store = SessionStore(config)
    store.save(mem)
    assert (tmp_path / f"session_{sid}.json").exists()

    fresh = PentestMemory("placeholder")
    assert store.resume(sid, fresh) is True
    assert fresh.target == "example.com"


def test_resume_missing_returns_false(tmp_path):
    store = SessionStore({"output": {"save_path": str(tmp_path)}})
    fresh = PentestMemory("x")
    assert store.resume("does_not_exist", fresh) is False
