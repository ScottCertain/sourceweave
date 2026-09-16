"""Tests for the model invocation boundary.

The `--bare` and API-key tests are the important ones. They guard the billing
invariant from ADR 0002, which is silent when it breaks: a run would simply
succeed and quietly bill against an API key instead of the subscription.
"""

from __future__ import annotations

import json
import subprocess

import pytest
from sourceweave_pipeline.claude_client import (
    PINNED_SETTINGS,
    ClaudeClient,
    ClaudeError,
    RateLimited,
)


@pytest.fixture
def settings(tmp_path):
    path = tmp_path / "claude-settings.json"
    path.write_text('{"permissions": {"deny": ["Bash"]}}', encoding="utf-8")
    return path


@pytest.fixture
def client(monkeypatch, settings):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/claude")
    return ClaudeClient("sonnet", throttle_seconds=0, settings_path=settings)


def _argv(client, **kwargs):
    return client._build_argv(
        "prompt",
        schema=kwargs.get("schema"),
        system_prompt_file=kwargs.get("system_prompt_file"),
        allowed_tools=kwargs.get("allowed_tools"),
    )


class TestBillingInvariants:
    """ADR 0002. Breaking either of these moves the project onto metered billing."""

    def test_never_passes_bare(self, client):
        assert "--bare" not in _argv(client)

    def test_never_passes_bare_in_unattended_mode(self, monkeypatch, settings):
        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/claude")
        unattended = ClaudeClient(
            "opus", throttle_seconds=0, unattended=True, settings_path=settings
        )
        assert "--bare" not in _argv(unattended)

    def test_strips_inherited_api_key(self, client, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-should-not-reach-the-subprocess")
        captured = {}

        def fake_run(argv, **kwargs):
            captured["env"] = kwargs["env"]
            return subprocess.CompletedProcess(
                argv, 0, json.dumps({"result": "ok", "session_id": "s1"}), ""
            )

        monkeypatch.setattr(subprocess, "run", fake_run)
        client.generate("draft something")

        assert "ANTHROPIC_API_KEY" not in captured["env"]

    def test_requires_cli_on_path(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda _: None)
        with pytest.raises(ClaudeError, match="not found on PATH"):
            ClaudeClient("opus")


class TestArgv:
    def test_includes_model_and_json_output(self, client):
        argv = _argv(client)
        assert argv[:3] == ["claude", "-p", "prompt"]
        assert "--model" in argv and "sonnet" in argv
        assert argv[argv.index("--output-format") + 1] == "json"

    def test_schema_is_serialized(self, client):
        schema = {"type": "object", "properties": {"score": {"type": "number"}}}
        argv = _argv(client, schema=schema)
        assert json.loads(argv[argv.index("--json-schema") + 1]) == schema

    def test_unattended_denies_prompts(self, monkeypatch, settings):
        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/claude")
        argv = _argv(
            ClaudeClient("opus", throttle_seconds=0, unattended=True, settings_path=settings)
        )
        assert argv[argv.index("--permission-mode") + 1] == "dontAsk"
        assert argv[argv.index("--permission-prompts") + 1] == "none"

    def test_supervised_runs_do_not_deny_prompts(self, client):
        assert "--permission-prompts" not in _argv(client)


class TestPinnedSettings:
    """ADR 0002 reproducibility mitigation. Runs must not inherit machine config."""

    def test_passes_settings_by_default(self, client, settings):
        argv = _argv(client)
        assert argv[argv.index("--settings") + 1] == str(settings)

    def test_the_shipped_pinned_file_exists(self, monkeypatch):
        # ADR 0002 documents --settings in the standard invocation shape.
        # This fails if the file it names is ever removed or renamed.
        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/claude")
        assert PINNED_SETTINGS.is_file()
        assert "--settings" in _argv(ClaudeClient("opus", throttle_seconds=0))

    def test_missing_settings_file_fails_loudly(self, monkeypatch, tmp_path):
        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/claude")
        with pytest.raises(ClaudeError, match="Pinned settings file not found"):
            ClaudeClient("opus", settings_path=tmp_path / "absent.json")

    def test_opting_out_is_possible_but_explicit(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/claude")
        argv = _argv(ClaudeClient("opus", throttle_seconds=0, settings_path=None))
        assert "--settings" not in argv


class TestParsing:
    def _run(self, client, monkeypatch, payload, returncode=0, stderr=""):
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda argv, **kw: subprocess.CompletedProcess(argv, returncode, payload, stderr),
        )
        return client.generate("go")

    def test_extracts_result_fields(self, client, monkeypatch):
        result = self._run(
            client,
            monkeypatch,
            json.dumps(
                {
                    "result": "the draft",
                    "session_id": "abc123",
                    "total_cost_usd": 0.0421,
                    "duration_ms": 8100,
                }
            ),
        )
        assert result.text == "the draft"
        assert result.session_id == "abc123"
        assert result.cost_usd == pytest.approx(0.0421)
        assert result.model == "sonnet"

    def test_rate_limit_raises_resumable_error(self, client, monkeypatch):
        with pytest.raises(RateLimited, match="Checkpoint and resume"):
            self._run(
                client,
                monkeypatch,
                json.dumps({"is_error": True, "result": "rate_limit exceeded"}),
                returncode=1,
            )

    def test_other_failures_raise_plain_error(self, client, monkeypatch):
        with pytest.raises(ClaudeError) as exc:
            self._run(
                client,
                monkeypatch,
                json.dumps({"is_error": True, "result": "model_not_found"}),
                returncode=1,
            )
        assert not isinstance(exc.value, RateLimited)

    def test_empty_output_reports_stderr(self, client, monkeypatch):
        with pytest.raises(ClaudeError, match="boom"):
            self._run(client, monkeypatch, "", returncode=1, stderr="boom")

    def test_evaluate_requires_structured_output(self, client, monkeypatch):
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda argv, **kw: subprocess.CompletedProcess(
                argv, 0, json.dumps({"result": "I scored it 8/10"}), ""
            ),
        )
        with pytest.raises(ClaudeError, match="Expected structured output"):
            client.evaluate("score this", {"type": "object"})

    def test_evaluate_returns_structured_output(self, client, monkeypatch):
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda argv, **kw: subprocess.CompletedProcess(
                argv, 0, json.dumps({"result": "", "structured_output": {"score": 0.82}}), ""
            ),
        )
        result = client.evaluate("score this", {"type": "object"})
        assert result.structured == {"score": 0.82}
