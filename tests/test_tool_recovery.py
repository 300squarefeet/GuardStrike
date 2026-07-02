from guardstrike.core import tool_recovery as tr


def test_classify_by_exit_code():
    assert tr.classify_error(124, "", None) == tr.TIMEOUT
    assert tr.classify_error(126, "", None) == tr.PERMISSION
    assert tr.classify_error(127, "", None) == tr.NOT_FOUND


def test_classify_by_output():
    assert tr.classify_error(1, "429 Too Many Requests", None) == tr.RATE_LIMITED
    assert tr.classify_error(1, "403 Forbidden", None) == tr.WAF_BLOCK
    assert tr.classify_error(1, "nmap: connection refused", None) == tr.CONNECTION
    assert tr.classify_error(1, "operation timed out", None) == tr.TIMEOUT
    assert tr.classify_error(1, "", "Permission denied") == tr.PERMISSION
    assert tr.classify_error(1, "all good", None) == tr.UNKNOWN


def test_is_retriable():
    for t in (tr.TIMEOUT, tr.RATE_LIMITED, tr.WAF_BLOCK, tr.CONNECTION):
        assert tr.is_retriable(t) is True
    for t in (tr.PERMISSION, tr.NOT_FOUND, tr.UNKNOWN):
        assert tr.is_retriable(t) is False


def test_backoff_grows_and_caps():
    assert tr.backoff_delay(0, tr.TIMEOUT) == 1.0
    assert tr.backoff_delay(1, tr.TIMEOUT) == 2.0
    # rate-limited starts higher than a plain timeout at the same attempt
    assert tr.backoff_delay(0, tr.RATE_LIMITED) > tr.backoff_delay(0, tr.TIMEOUT)
    assert tr.backoff_delay(10, tr.RATE_LIMITED, cap=30.0) == 30.0


def test_adjust_params_downshift():
    out = tr.adjust_params("httpx", tr.RATE_LIMITED, {"threads": 10})
    assert out["threads"] == 5 and out["delay"] >= 1
    # input not mutated
    src = {"threads": 8}
    tr.adjust_params("httpx", tr.TIMEOUT, src)
    assert src == {"threads": 8}
    # per-tool table (nmap timing) applied on timeout even with no knobs
    assert tr.adjust_params("nmap", tr.TIMEOUT, {})["timing"] == "-T2"
    # non-retriable-ish / threads==1 stays >= 1
    assert tr.adjust_params("httpx", tr.TIMEOUT, {"threads": 1})["threads"] == 1


def test_permission_wins_over_incidental_timeout():
    # Reordered markers: a real permission failure isn't masked by an echoed "timeout: 30".
    assert tr.classify_error(1, "timeout: 30\npermission denied", None) == tr.PERMISSION
