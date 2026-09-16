"""Tests for provenance records.

Staleness detection is what makes regeneration incremental, which ADR 0002
promotes from a cost optimization to a functional requirement.
"""

from __future__ import annotations

import yaml
from sourceweave_pipeline.provenance import Provenance, ambient_fingerprint, source_ref


def _provenance(**overrides):
    defaults = {
        "target": "anythingllm",
        "upstream_version": "v1.16.1",
        "upstream_commit": "0" * 40,
        "model": "opus",
        "prompt_version": "api-reference@1",
    }
    return Provenance(**{**defaults, **overrides})


class TestSourceRef:
    def test_digests_a_real_file(self, tmp_path):
        (tmp_path / "openapi.json").write_text('{"openapi": "3.0.0"}', encoding="utf-8")
        ref = source_ref(tmp_path, "openapi.json")
        assert ref.path == "openapi.json"
        assert len(ref.sha256) == 64

    def test_missing_file_raises(self, tmp_path):
        try:
            source_ref(tmp_path, "nope.json")
        except FileNotFoundError as exc:
            assert "pinned upstream" in str(exc)
        else:
            raise AssertionError("expected FileNotFoundError")


class TestStaleness:
    def test_unchanged_source_is_not_stale(self, tmp_path):
        (tmp_path / "a.js").write_text("original", encoding="utf-8")
        prov = _provenance(sources=[source_ref(tmp_path, "a.js")])
        assert prov.is_stale(tmp_path) is False

    def test_changed_source_is_stale(self, tmp_path):
        (tmp_path / "a.js").write_text("original", encoding="utf-8")
        prov = _provenance(sources=[source_ref(tmp_path, "a.js")])

        (tmp_path / "a.js").write_text("upstream changed this", encoding="utf-8")
        assert prov.is_stale(tmp_path) is True

    def test_deleted_source_is_stale(self, tmp_path):
        (tmp_path / "a.js").write_text("original", encoding="utf-8")
        prov = _provenance(sources=[source_ref(tmp_path, "a.js")])

        (tmp_path / "a.js").unlink()
        assert prov.is_stale(tmp_path) is True

    def test_one_changed_file_among_many_is_stale(self, tmp_path):
        for name in ("a.js", "b.js", "c.js"):
            (tmp_path / name).write_text(name, encoding="utf-8")
        prov = _provenance(sources=[source_ref(tmp_path, n) for n in ("a.js", "b.js", "c.js")])

        (tmp_path / "b.js").write_text("changed", encoding="utf-8")
        assert prov.is_stale(tmp_path) is True


class TestAmbientFingerprint:
    """Partial mitigation for the reproducibility gap in ADR 0002.

    Makes environment drift detectable after the fact. It cannot prevent drift
    in ambient config this project does not control.
    """

    def _repo(self, tmp_path, claude_md="rules", settings='{"a": 1}'):
        tmp_path.mkdir(parents=True, exist_ok=True)
        (tmp_path / "CLAUDE.md").write_text(claude_md, encoding="utf-8")
        (tmp_path / "pipeline").mkdir(exist_ok=True)
        (tmp_path / "pipeline" / "claude-settings.json").write_text(settings, encoding="utf-8")
        return tmp_path

    def test_is_stable_for_unchanged_inputs(self, tmp_path):
        repo = self._repo(tmp_path)
        assert ambient_fingerprint(repo) == ambient_fingerprint(repo)

    def test_changes_when_claude_md_changes(self, tmp_path):
        repo = self._repo(tmp_path)
        before = ambient_fingerprint(repo)

        (repo / "CLAUDE.md").write_text("different rules", encoding="utf-8")
        assert ambient_fingerprint(repo) != before

    def test_changes_when_pinned_settings_change(self, tmp_path):
        repo = self._repo(tmp_path)
        before = ambient_fingerprint(repo)

        (repo / "pipeline" / "claude-settings.json").write_text('{"a": 2}', encoding="utf-8")
        assert ambient_fingerprint(repo) != before

    def test_ignores_interactive_settings(self, tmp_path):
        """Approving a permission by hand must not invalidate existing pages.

        Claude Code writes .claude/settings.json itself. Including it would
        report drift across the whole corpus for a change that never touched
        generation.
        """
        repo = self._repo(tmp_path)
        before = ambient_fingerprint(repo)

        (repo / ".claude").mkdir(exist_ok=True)
        (repo / ".claude" / "settings.json").write_text(
            '{"permissions": {"allow": ["Bash(ls)"]}}', encoding="utf-8"
        )
        assert ambient_fingerprint(repo) == before

    def test_changes_when_an_input_is_removed(self, tmp_path):
        repo = self._repo(tmp_path)
        before = ambient_fingerprint(repo)

        (repo / "CLAUDE.md").unlink()
        assert ambient_fingerprint(repo) != before

    def test_works_when_no_inputs_are_present(self, tmp_path):
        assert len(ambient_fingerprint(tmp_path)) == 16

    def test_content_cannot_be_shifted_between_inputs(self, tmp_path):
        """Field separators keep two inputs from being confused for each other."""
        a = self._repo(tmp_path / "a", claude_md="xy", settings="z")
        b = self._repo(tmp_path / "b", claude_md="x", settings="yz")
        assert ambient_fingerprint(a) != ambient_fingerprint(b)


class TestFrontMatter:
    def test_round_trips_as_yaml(self, tmp_path):
        (tmp_path / "openapi.json").write_text("{}", encoding="utf-8")
        prov = _provenance(sources=[source_ref(tmp_path, "openapi.json")])

        block = prov.to_front_matter()
        assert block.startswith("---\n")
        assert block.endswith("---\n")

        parsed = yaml.safe_load(block.strip("-\n"))["sourceweave"]
        assert parsed["upstream_version"] == "v1.16.1"
        assert parsed["prompt_version"] == "api-reference@1"
        assert parsed["sources"][0]["path"] == "openapi.json"

    def test_discloses_ai_generation_by_default(self):
        assert _provenance().ai_generated is True

    def test_unreviewed_by_default(self):
        # A page with reviewed_by unset must not be published.
        assert _provenance().reviewed_by is None
