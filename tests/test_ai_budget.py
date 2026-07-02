import logging

import pytest

from guardstrike.ai.budget import (
    BudgetTracker,
    CostBudgetExceeded,
    TokenBudgetExceeded,
)
from guardstrike.ai.providers.base_provider import TokenBudgetExceeded as ReexportedTBE

LOG = logging.getLogger("t")


def test_no_caps_never_raises():
    t = BudgetTracker(None, None, LOG)
    for _ in range(5):
        t.add(1_000_000, 1000.0)
    assert t.used_tokens == 5_000_000


def test_token_cap_raises_at_100pct():
    t = BudgetTracker(1000, None, LOG)
    t.add(800, 0.0)  # 80% — warns, no raise
    with pytest.raises(TokenBudgetExceeded):
        t.add(300, 0.0)  # crosses 1000


def test_cost_cap_raises_at_100pct():
    t = BudgetTracker(None, 1.0, LOG)
    t.add(10, 0.80)
    with pytest.raises(CostBudgetExceeded):
        t.add(10, 0.30)  # crosses 1.0 USD


def test_shared_tracker_accumulates_across_callers():
    t = BudgetTracker(1000, None, LOG)
    t.add(600, 0.0)
    with pytest.raises(TokenBudgetExceeded):
        t.add(600, 0.0)  # 1200 > 1000 — second caller pushes it over
    assert t.used_tokens == 1200


def test_token_budget_exceeded_reexported_from_base_provider():
    # Back-compat: tests/test_provider_base.py imports it from here.
    assert ReexportedTBE is TokenBudgetExceeded


def test_enforce_delegates_to_tracker(monkeypatch):
    # A provider's _enforce_token_budget must hit the shared tracker.
    from guardstrike.ai.budget import BudgetTracker

    class _Stub:
        budget = BudgetTracker(100, None, LOG)
        from guardstrike.ai.providers.base_provider import BaseProvider

        _enforce_token_budget = BaseProvider._enforce_token_budget

    s = _Stub()
    with pytest.raises(TokenBudgetExceeded):
        s._enforce_token_budget(150, 0.0)
