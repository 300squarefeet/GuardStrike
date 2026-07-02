from pathlib import Path

from guardstrike.utils import resources


def test_builtin_workflows_dir_has_yaml():
    d = resources.builtin_workflows_dir()
    assert d.is_dir()
    assert any(d.glob("*.yaml"))


def test_find_workflow_exact_and_fuzzy():
    assert resources.find_workflow("recon") is not None
    # fuzzy: "web" should resolve to some web_*.yaml
    assert resources.find_workflow("web") is not None
    assert resources.find_workflow("definitely_missing_xyz") is None


def test_user_workflow_overrides_builtin(tmp_path, monkeypatch):
    user_dir = tmp_path / ".guardstrike" / "workflows"
    user_dir.mkdir(parents=True)
    (user_dir / "recon.yaml").write_text("name: user_recon\nsteps: []\n")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    found = resources.find_workflow("recon")
    assert found is not None
    assert found.read_text().startswith("name: user_recon")


def test_default_config_path_exists():
    assert resources.default_config_path().is_file()
