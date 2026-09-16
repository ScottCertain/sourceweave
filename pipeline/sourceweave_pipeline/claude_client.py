"""The single point of contact between SourceWeave and a language model.

Every model invocation in this project goes through this module. Nothing else
shells out to ``claude``, and nothing anywhere imports an Anthropic SDK.

Two constraints from ADR 0002 are enforced here rather than left to callers:

1. ``--bare`` is never passed. Bare mode does not read subscription
   credentials and falls back to ``ANTHROPIC_API_KEY``. What makes this worth
   a guard is that it fails *silently*: adding the flag raises no error, and
   the run simply executes against a different credential path with nothing
   in the output saying so.

2. Runs are throttled and resumable. A fixed capacity ceiling is the binding
   constraint, so invocations are spaced, and a run that reaches the ceiling
   raises ``RateLimited`` so the caller can checkpoint and stop rather than
   retry into a wall.

See docs/decisions/0002-model-access-via-claude-subscription.md.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "PINNED_SETTINGS",
    "ClaudeClient",
    "ClaudeError",
    "ClaudeResult",
    "RateLimited",
]

PINNED_SETTINGS = Path(__file__).resolve().parents[1] / "claude-settings.json"
"""Settings passed explicitly to every invocation.

Because ``--bare`` cannot be used, a run would otherwise inherit whatever is
configured on the machine. Pinning settings narrows that surface to something
the commit controls. The file is digested into ``Provenance.ambient_context``,
so changing it is visible in every page generated afterwards.
"""


class ClaudeError(RuntimeError):
    """A model invocation failed."""


class RateLimited(ClaudeError):
    """The subscription rate limit was reached.

    Callers should checkpoint and stop, not retry in a tight loop. A run that
    stops here is resumable; completed pages are already on disk.
    """


@dataclass(frozen=True)
class ClaudeResult:
    """One completed invocation."""

    text: str
    """The model's final response. Empty when ``structured`` is populated."""

    structured: dict[str, Any] | None
    """Parsed ``structured_output``, present when a JSON schema was supplied."""

    session_id: str | None
    model: str

    cost_usd: float | None
    """Client-side cost *estimate* reported by the CLI.

    Nothing is billed -- runs draw on the subscription. This is recorded as a
    proxy for run weight in provenance and quality-trend data (PRD FR-15).
    """

    duration_ms: int | None
    raw: dict[str, Any] = field(repr=False, default_factory=dict)


class ClaudeClient:
    """Invokes the Claude Code CLI in print mode.

    Args:
        model: Model alias, e.g. ``"opus"`` or ``"sonnet"``. Generation and
            evaluation deliberately use different tiers (ADR 0002).
        cwd: Working directory for the invocation. Set this to the directory
            holding the grounded source so relative paths in prompts resolve.
        throttle_seconds: Minimum gap between invocations.
        timeout_seconds: Per-invocation timeout.
        unattended: When true, deny anything that would prompt and never wait
            for a permission host. Leave false for supervised local runs.
        settings_path: Settings file passed with ``--settings``. Defaults to
            the pinned file. Passing ``None`` means the run inherits ambient
            settings, which weakens reproducibility -- only do so deliberately.
    """

    def __init__(
        self,
        model: str,
        *,
        cwd: Path | None = None,
        throttle_seconds: float = 2.0,
        timeout_seconds: int = 600,
        unattended: bool = False,
        settings_path: Path | None = PINNED_SETTINGS,
    ) -> None:
        self.model = model
        self.cwd = cwd
        self.throttle_seconds = throttle_seconds
        self.timeout_seconds = timeout_seconds
        self.unattended = unattended
        self.settings_path = settings_path
        self._last_call_at: float | None = None

        if shutil.which("claude") is None:
            raise ClaudeError(
                "The 'claude' CLI was not found on PATH. SourceWeave uses the "
                "Claude Code CLI for model access rather than an API key; see "
                "docs/decisions/0002-model-access-via-claude-subscription.md"
            )

        if settings_path is not None and not settings_path.is_file():
            raise ClaudeError(
                f"Pinned settings file not found: {settings_path}. Runs would "
                f"silently fall back to ambient settings, which breaks the "
                f"reproducibility guarantee in ADR 0002. Pass settings_path=None "
                f"to accept that deliberately."
            )

    # -- public API ---------------------------------------------------------

    def generate(
        self,
        prompt: str,
        *,
        system_prompt_file: Path | None = None,
        allowed_tools: list[str] | None = None,
    ) -> ClaudeResult:
        """Draft prose. Returns text."""
        return self._invoke(
            prompt,
            system_prompt_file=system_prompt_file,
            allowed_tools=allowed_tools,
        )

    def evaluate(
        self,
        prompt: str,
        schema: dict[str, Any],
        *,
        system_prompt_file: Path | None = None,
    ) -> ClaudeResult:
        """Score output against a schema. Returns structured data.

        The schema makes scoring machine-readable, which is what lets
        evaluation results aggregate into trends (PRD FR-11, FR-12, FR-15).
        """
        result = self._invoke(prompt, system_prompt_file=system_prompt_file, schema=schema)
        if result.structured is None:
            raise ClaudeError(
                f"Expected structured output against the supplied schema, got none. "
                f"Response text: {result.text[:200]!r}"
            )
        return result

    # -- internals ----------------------------------------------------------

    def _build_argv(
        self,
        prompt: str,
        *,
        schema: dict[str, Any] | None,
        system_prompt_file: Path | None,
        allowed_tools: list[str] | None,
    ) -> list[str]:
        # NOTE: '--bare' must never appear in this list. See module docstring.
        argv = [
            "claude",
            "-p",
            prompt,
            "--model",
            self.model,
            "--output-format",
            "json",
        ]

        if self.settings_path is not None:
            argv += ["--settings", str(self.settings_path)]

        if schema is not None:
            argv += ["--json-schema", json.dumps(schema)]

        if system_prompt_file is not None:
            argv += ["--append-system-prompt-file", str(system_prompt_file)]

        if allowed_tools:
            argv += ["--allowedTools", ",".join(allowed_tools)]

        if self.unattended:
            argv += ["--permission-mode", "dontAsk", "--permission-prompts", "none"]

        return argv

    def _throttle(self) -> None:
        if self._last_call_at is None:
            return
        elapsed = time.monotonic() - self._last_call_at
        remaining = self.throttle_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def _invoke(
        self,
        prompt: str,
        *,
        schema: dict[str, Any] | None = None,
        system_prompt_file: Path | None = None,
        allowed_tools: list[str] | None = None,
    ) -> ClaudeResult:
        self._throttle()
        argv = self._build_argv(
            prompt,
            schema=schema,
            system_prompt_file=system_prompt_file,
            allowed_tools=allowed_tools,
        )

        # Strip any inherited API key. If one is set in the environment the CLI
        # may prefer it over the subscription login, silently moving the run
        # onto metered billing -- the exact outcome ADR 0002 exists to avoid.
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}

        try:
            proc = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self.timeout_seconds,
                cwd=self.cwd,
                env=env,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ClaudeError(f"Invocation exceeded {self.timeout_seconds}s") from exc
        finally:
            self._last_call_at = time.monotonic()

        return self._parse(proc)

    def _parse(self, proc: subprocess.CompletedProcess[str]) -> ClaudeResult:
        stdout = (proc.stdout or "").strip()

        if not stdout:
            stderr = (proc.stderr or "").strip()
            raise ClaudeError(f"No output (exit {proc.returncode}). stderr: {stderr[:500]}")

        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as exc:
            # A failure inside the run is reported as the result on stdout, so
            # unparseable output usually means the CLI itself failed to start.
            raise ClaudeError(f"Could not parse CLI output: {stdout[:500]}") from exc

        if payload.get("is_error") or proc.returncode != 0:
            message = str(payload.get("result") or payload.get("error") or "unknown error")
            if "rate_limit" in message or "rate limit" in message.lower():
                raise RateLimited(
                    f"Subscription rate limit reached. Checkpoint and resume later. ({message})"
                )
            raise ClaudeError(f"Invocation failed (exit {proc.returncode}): {message[:500]}")

        return ClaudeResult(
            text=payload.get("result") or "",
            structured=payload.get("structured_output"),
            session_id=payload.get("session_id"),
            model=self.model,
            cost_usd=payload.get("total_cost_usd"),
            duration_ms=payload.get("duration_ms"),
            raw=payload,
        )
