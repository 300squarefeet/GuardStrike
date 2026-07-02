from guardstrike.utils.helpers import mask_secrets


def test_masks_truthy_secret():
    assert mask_secrets({"ai": {"api_key": "sk-123"}}) == {"ai": {"api_key": "***"}}


def test_leaves_null_and_nonsecret():
    src = {"ai": {"api_key": None, "provider": "gemini"}}
    assert mask_secrets(src) == {"ai": {"api_key": None, "provider": "gemini"}}


def test_nested_and_lists():
    src = {"a": [{"token": "t"}, {"x": 1}], "b": {"c": {"password": "p"}}}
    out = mask_secrets(src)
    assert out == {"a": [{"token": "***"}, {"x": 1}], "b": {"c": {"password": "***"}}}


def test_does_not_mutate_input():
    src = {"ai": {"api_key": "sk-123"}}
    mask_secrets(src)
    assert src == {"ai": {"api_key": "sk-123"}}


def test_case_insensitive_key():
    assert mask_secrets({"API_KEY": "x"}) == {"API_KEY": "***"}


def test_substring_secret_keys_masked():
    # Realistic prefixed/suffixed secret keys must not leak.
    src = {
        "openai_api_key": "sk-a",
        "client_secret": "cs-b",
        "access_token": "at-c",
        "slack_webhook": "https://hook",
    }
    out = mask_secrets(src)
    assert out == {
        "openai_api_key": "***",
        "client_secret": "***",
        "access_token": "***",
        "slack_webhook": "***",
    }
    assert "sk-a" not in str(out) and "cs-b" not in str(out)
