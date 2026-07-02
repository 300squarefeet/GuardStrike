from guardstrike.ai.providers.base_provider import TRANSIENT_MARKERS, BaseProvider


def test_503_without_leading_space_is_retriable():
    # Regression: "503 service unavailable" (no leading space) must retry.
    assert BaseProvider.default_is_retriable(Exception("503 Service Unavailable")) is True


def test_common_transients_retriable():
    for msg in (
        "429 Too Many Requests",
        "rate limit exceeded",
        "gateway timeout",
        "502 Bad Gateway",
    ):
        assert BaseProvider.default_is_retriable(Exception(msg)) is True


def test_non_transient_not_retriable():
    assert BaseProvider.default_is_retriable(Exception("invalid api key")) is False


def test_markers_shared_with_ai_client():
    from guardstrike.ai.ai_client import _TRANSIENT_MARKERS

    assert _TRANSIENT_MARKERS is TRANSIENT_MARKERS
