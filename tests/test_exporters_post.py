import urllib.error
import urllib.request

import pytest

from guardstrike.core.exporters import defectdojo, slack


class _FakeResp:
    def __init__(self, code):
        self.status = code

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _capture(monkeypatch, code=201):
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["req"] = req
        captured["timeout"] = timeout
        return _FakeResp(code)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    return captured


def test_defectdojo_post_success(monkeypatch):
    cap = _capture(monkeypatch, 201)
    status = defectdojo.post("https://dd.example.com/", "tok", 7, {"findings": [1]})
    assert status == 201
    req = cap["req"]
    assert req.full_url == "https://dd.example.com/api/v2/import-scan/"
    assert req.get_header("Authorization") == "Token tok"
    body = req.data
    assert b"Generic Findings Import" in body
    assert b'name="engagement"' in body and b"7" in body
    assert b'name="file"; filename="findings.json"' in body
    assert b'"findings": [1]' in body or b'"findings":[1]' in body
    # DefectDojo needs active=true for imported findings to appear
    assert b'name="active"' in body and b"true" in body
    assert b'name="verified"' in body
    # boundary in the Content-Type header MUST match the delimiter in the body
    ctype = req.get_header("Content-type")
    assert ctype.startswith("multipart/form-data; boundary=")
    boundary = ctype.split("boundary=", 1)[1]
    assert ("--" + boundary).encode() in body
    # default timeout is forwarded
    assert cap["timeout"] == 30


def test_defectdojo_post_normalizes_base_url(monkeypatch):
    cap = _capture(monkeypatch, 201)
    defectdojo.post("https://dd.example.com", "tok", 1, {"findings": []})  # no trailing slash
    assert cap["req"].full_url == "https://dd.example.com/api/v2/import-scan/"


def test_defectdojo_post_propagates_error(monkeypatch):
    def boom(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 500, "err", {}, None)

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    with pytest.raises(urllib.error.HTTPError):
        defectdojo.post("https://dd.example.com", "tok", 1, {"findings": []})


def test_slack_post(monkeypatch):
    cap = _capture(monkeypatch, 200)
    status = slack.post("https://hooks.example.com/xyz", {"text": "hi"})
    assert status == 200
    req = cap["req"]
    assert req.full_url == "https://hooks.example.com/xyz"
    assert req.get_header("Content-type") == "application/json"
    assert req.data == b'{"text": "hi"}'
