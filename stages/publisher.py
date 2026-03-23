"""
Stage 8: Ghost CMS Publisher

Source: christancho/Blogging-with-CrewAI — JWT auth, Ghost Admin API, draft status.

Converts Markdown → HTML and publishes to Ghost CMS as a draft post.
All Ghost API logic lives in tools.GhostCMSTool — this stage is a thin wrapper
that extracts the right fields from PipelineContext and calls the tool.

Output written to: ctx.publish_result (Dict)
  Keys: status, post_id, post_url, draft_url (on success)
        status, message (on error)
"""

from __future__ import annotations

import json
from typing import Dict, Optional, TYPE_CHECKING

from interfaces import PipelineStage
from tools import GhostCMSTool

if TYPE_CHECKING:
    from context import PipelineContext


class PublisherStage(PipelineStage):
    """
    Publish final article to Ghost CMS as a draft.

    Source: christancho/Blogging-with-CrewAI.
    """

    name = "publisher"

    def __init__(self, llm=None, config: Optional[Dict] = None):
        # llm is not used — publishing is a deterministic API call
        self._config = config or {}
        self._tool = GhostCMSTool()

    def run(self, ctx: "PipelineContext") -> "PipelineContext":
        content = ctx.final_content

        if not content:
            ctx.record_error(self.name, "no content to publish")
            return ctx

        payload = json.dumps({
            "title": ctx.meta_title,
            "content": content,
            "meta_description": ctx.meta_description,
            "tags": ctx.tags,
        })

        raw_result = self._tool._run(payload)

        try:
            ctx.publish_result = json.loads(raw_result)
        except Exception:
            ctx.publish_result = {"status": "error", "raw": raw_result}

        return ctx

    def quality_gate(self, ctx: "PipelineContext") -> None:
        assert ctx.publish_result is not None, "publish_result must not be None"
        status = ctx.publish_result.get("status")
        assert status == "success", (
            f"Ghost publish failed: {ctx.publish_result.get('message', 'unknown error')}"
        )
