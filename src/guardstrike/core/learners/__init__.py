"""Sub-package: offline learners (A5).

Provides the trainable, telemetry-driven helpers that complement the
LLM-driven decision agents. ``tool_ranker.ToolRanker`` is the only
member today — predicts which tool to run next given (phase,
target_type, prior counts), with a fallback path when the model is not
yet confident.

Models are pickled under ``~/.guardstrike/`` and loaded lazily — GuardStrike
runs identically without one.
"""
