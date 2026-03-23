"""
LLM wrapper with Anthropic model fallback chain.
Pattern from Nimish-0070/AI-CONTENT-GENERATOR-AGENT, adapted for Anthropic Claude.

Fallback order: claude-opus-4-6 → claude-sonnet-4-6 → claude-haiku-4-5-20251001
Used by the manual fallback pipeline when CrewAI is unavailable.
"""

import os
import time
import random
from typing import Optional


class AnthropicLLM:
    """
    Anthropic LLM wrapper with per-model retry and model-level fallback.

    On transient errors (429, overloaded, 503) retries with exponential backoff.
    On non-retryable errors falls through to the next model in the chain.
    Returns "LLM_UNAVAILABLE" only after all models are exhausted.
    """

    def __init__(self, models: Optional[list] = None):
        self._models = models or [
            "claude-opus-4-6",
            "claude-sonnet-4-6",
            "claude-haiku-4-5-20251001",
        ]
        self._client = None  # lazy init so import doesn't hard-fail if anthropic absent

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
                api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("LLM_API_KEY")
                self._client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                raise RuntimeError(
                    "anthropic package not installed. Run: pip install anthropic"
                )
        return self._client

    def _call_once(self, model: str, prompt: str, max_tokens: int) -> str:
        client = self._get_client()
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def run(self, prompt: str, max_retries: int = 2, max_tokens: int = 4096) -> str:
        """
        Run prompt through the model fallback chain.
        Returns the first successful response, or "LLM_UNAVAILABLE" if all fail.
        """
        for model in self._models:
            retry = 0
            while retry <= max_retries:
                try:
                    result = self._call_once(model, prompt, max_tokens)
                    return result
                except Exception as e:
                    err = str(e).lower()
                    transient = any(
                        tok in err
                        for tok in (
                            "429", "overloaded", "rate_limit", "rate limit",
                            "overload", "503", "service_unavailable", "resource_exhausted",
                        )
                    )
                    if transient and retry < max_retries:
                        wait = (2 ** retry) + random.random()
                        print(
                            f"[AnthropicLLM] transient error on {model} "
                            f"(attempt {retry + 1}): {e}; retrying in {wait:.1f}s"
                        )
                        time.sleep(wait)
                        retry += 1
                        continue
                    print(f"[AnthropicLLM] error on {model}: {e} — trying next model")
                    break  # move to next model
            print(f"[AnthropicLLM] model {model} exhausted retries.")
        return "LLM_UNAVAILABLE"


# Module-level singleton — import and use directly in the manual fallback pipeline
llm = AnthropicLLM()
