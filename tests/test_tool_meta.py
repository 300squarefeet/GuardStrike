from guardstrike.core.tool_meta import TOOL_META, tool_summary


def test_known_tool_has_description_and_category():
    s = tool_summary("nmap")
    assert s["description"]
    assert s["category"]


def test_unknown_tool_defaults():
    assert tool_summary("totally-unknown-xyz") == {"description": "", "category": "other"}


def test_meta_entries_shape():
    for name, meta in TOOL_META.items():
        assert set(meta) == {"description", "category"}
        assert meta["description"] and meta["category"]
