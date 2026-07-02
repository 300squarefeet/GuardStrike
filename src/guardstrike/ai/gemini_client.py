"""
Backward compatibility wrapper for GeminiClient
Redirects to the new AIClient with provider support
"""

from guardstrike.ai.ai_client import AIClient

# Backward compatibility
GeminiClient = AIClient

__all__ = ["GeminiClient", "AIClient"]
