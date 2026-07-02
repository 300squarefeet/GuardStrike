import logging

from guardstrike.core.workflow.loader import WorkflowLoader


def test_loads_known_workflow():
    loader = WorkflowLoader(logging.getLogger("t"))
    doc = loader.load_doc("recon")
    assert isinstance(doc, dict)
    assert doc.get("steps")


def test_unknown_workflow_returns_fallback():
    loader = WorkflowLoader(logging.getLogger("t"))
    doc = loader.load_doc("definitely_missing_xyz")
    assert doc["name"] == "fallback"
