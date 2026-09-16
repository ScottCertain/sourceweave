"""Provenance records for generated pages.

Every generated page carries a record of what produced it: which source files
it was grounded in, which upstream version it describes, which model and prompt
version drafted it (PRD FR-7). Provenance is what makes a page auditable and
what makes regeneration decisions possible -- a page is stale when the source
files it names have changed.

The record is written as YAML front matter in the page itself, so it survives
the trip through Docusaurus and can be surfaced on the rendered page.
"""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import yaml

__all__ = [
    "Provenance",
    "SourceRef",
    "ambient_fingerprint",
    "pinned_version",
    "source_ref",
]

AMBIENT_INPUTS = ("CLAUDE.md", "pipeline/claude-settings.json")
"""Version-controlled inputs that govern a generation run.

Both are pinned by the commit: ``CLAUDE.md`` loads ambiently and cannot be
turned off without ``--bare`` (ADR 0002), and the settings file is passed
explicitly with ``--settings``.

``.claude/settings.json`` is deliberately **not** listed. It governs
interactive work in the repository, and Claude Code writes to it on its own
when a permission is approved. Including it would flip the fingerprint of every
previously generated page whenever someone approved a tool by hand -- drift
reported for a reason that never touched generation.

Not exhaustive by construction. A run still loads configuration this project
does not control, such as a contributor's ``~/.claude``. The fingerprint makes
drift in the inputs we *can* see detectable; it does not prevent drift in the
ones we cannot.
"""


@dataclass(frozen=True)
class SourceRef:
    """One source file a page was grounded in."""

    path: str
    """Path relative to the target's upstream submodule root."""

    sha256: str
    """Digest of the file's contents when the page was generated.

    A page is stale when this no longer matches, which is what drives
    incremental regeneration (ADR 0002 -- rate limits make full-corpus
    regeneration impractical).
    """


@dataclass
class Provenance:
    """What produced a generated page."""

    target: str
    """Target name, e.g. 'anythingllm'."""

    upstream_version: str
    """Release tag of the pinned upstream, e.g. 'v1.16.1'. This is the version
    the page describes, and is surfaced on the rendered page (PRD FR-19)."""

    upstream_commit: str
    """Exact commit the submodule pointed at."""

    model: str
    """Model alias used for generation."""

    prompt_version: str
    """Identifier of the prompt that drafted this page. Pinning this is what
    makes a build reproducible from a commit (PRD NFR-2)."""

    sources: list[SourceRef] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    generator: str = "sourceweave"
    ai_generated: bool = True
    """Always true. Surfaced as the per-page AI disclosure (PRD FR-23)."""

    reviewed_by: str | None = None
    """Set during human review. A page with this unset has not been reviewed
    and must not be published (PRD non-goal: no fully autonomous publishing)."""

    cost_usd_estimate: float | None = None
    """Client-side estimate, not a bill. See ClaudeResult.cost_usd."""

    ambient_context: str | None = None
    """Digest of the ambient inputs in effect when this page was generated.

    Partial mitigation for the reproducibility gap in ADR 0002: because
    ``--bare`` cannot be used, the machine contributes to every run. A page
    whose fingerprint differs from the current environment was generated under
    different conditions -- detectable after the fact, not prevented.
    """

    def to_front_matter(self) -> str:
        """Render as a YAML front-matter block."""
        body = yaml.safe_dump(
            {"sourceweave": asdict(self)},
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )
        return f"---\n{body}---\n"

    def is_stale(self, upstream_root: Path) -> bool:
        """True when any recorded source file has changed on disk."""
        return any(
            not (upstream_root / ref.path).is_file()
            or _digest(upstream_root / ref.path) != ref.sha256
            for ref in self.sources
        )


def ambient_fingerprint(repo_root: Path) -> str:
    """Digest the ambient context that contributes to a generation run.

    Covers the version-controlled inputs in ``AMBIENT_INPUTS``. A missing file
    is folded into the digest as absent rather than skipped, so adding or
    removing one changes the fingerprint.

    Returns a short hex digest suitable for ``Provenance.ambient_context``.
    """
    digest = hashlib.sha256()
    for name in AMBIENT_INPUTS:
        path = repo_root / name
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes() if path.is_file() else b"<absent>")
        digest.update(b"\0")
    return digest.hexdigest()[:16]


def source_ref(upstream_root: Path, relative_path: str) -> SourceRef:
    """Build a SourceRef for one file under the pinned upstream."""
    full = upstream_root / relative_path
    if not full.is_file():
        raise FileNotFoundError(f"Source file not found under pinned upstream: {full}")
    return SourceRef(path=relative_path, sha256=_digest(full))


def pinned_version(submodule_path: Path) -> tuple[str, str]:
    """Return ``(tag_or_describe, commit_sha)`` for a pinned submodule.

    Raises if the submodule is not initialized, because generating against an
    empty directory would silently produce ungrounded output.
    """
    if not (submodule_path / ".git").exists():
        raise RuntimeError(
            f"Submodule not initialized at {submodule_path}. "
            f"Run: git submodule update --init {submodule_path}"
        )

    commit = _git(submodule_path, "rev-parse", "HEAD")
    try:
        version = _git(submodule_path, "describe", "--tags", "--exact-match")
    except subprocess.CalledProcessError:
        # Not on a tag -- a master-tracking preview build (PRD FR-20).
        version = f"{_git(submodule_path, 'rev-parse', '--abbrev-ref', 'HEAD')}@{commit[:12]}"
    return version, commit


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
