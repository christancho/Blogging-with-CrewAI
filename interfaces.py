"""
Stage interface for the semantic SEO pipeline.

Every stage is a PipelineStage — it receives PipelineContext, does its work,
and returns an updated PipelineContext. Stages are swappable: the orchestrator
doesn't care which implementation sits behind the interface.

Implementation contract:
- __init__(llm, config) — LLM injected via constructor (Nimish DI pattern)
- run(ctx) → ctx       — reads from ctx, writes results, returns ctx
- quality_gate(ctx)    — asserts post-conditions (soft gate, orchestrator catches)
- name                 — string identifier used in logs and timings

Source pattern: MathWizz pure-method-chain made explicit with an ABC.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from context import PipelineContext


class PipelineStage(ABC):
    """
    Abstract base class for all pipeline stages.

    All stages follow the same contract so the orchestrator can run any sequence
    of stages without knowing their internal implementations.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Stage identifier — used in logs, timings, and quality gate messages."""
        ...

    @abstractmethod
    def run(self, ctx: "PipelineContext") -> "PipelineContext":
        """
        Execute this stage.

        Reads relevant fields from ctx, performs work, writes results back to ctx.
        Must never raise unhandled exceptions — catch internally and call
        ctx.record_error() to log problems without aborting the pipeline.
        Returns the updated ctx.
        """
        ...

    def quality_gate(self, ctx: "PipelineContext") -> None:
        """
        Assert post-conditions after this stage runs.

        Raise AssertionError with a descriptive message if the output doesn't
        meet minimum structural requirements. The orchestrator catches this,
        logs it, and continues (soft gate — does not abort the pipeline).

        Override in stages where output quality can be verified structurally.
        Default: no-op (gate always passes).
        """
