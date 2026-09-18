"""Compare two OpenAPI specs and report what changed.

FR-3 asks for docs-affecting changes on ``master`` to be noticed between
releases. ADR 0003 reduces that to diffing ``server/swagger/openapi.json``
between the pinned tag and ``master`` -- a structured diff on a structured
file, rather than heuristics over prose.

Three signals, not one. Measuring the pinned v1.16.1 spec against ``master``
found the same 63 endpoints on both sides and a spec that was not identical:
three endpoint *definitions* had changed. A comparison that only looked at
which endpoints exist would have reported no drift and been wrong.

Target-agnostic: this compares two OpenAPI documents and knows nothing about
AnythingLLM (PRD NFR-5).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = ["OpenApiDrift", "compare", "main", "to_markdown"]

# Keys under a path item that are operations rather than metadata.
_HTTP_METHODS = frozenset({"get", "put", "post", "delete", "options", "head", "patch", "trace"})


@dataclass(frozen=True)
class OpenApiDrift:
    """What changed between two OpenAPI specs."""

    added: tuple[str, ...] = ()
    removed: tuple[str, ...] = ()
    changed: tuple[str, ...] = ()

    changed_shared: tuple[str, ...] = ()
    """Paths whose *shared* definition changed -- the path-item keys that sit
    beside the methods, chiefly ``parameters``.

    This has its own field because it falls between the other two checks: it
    is not an operation, so the operation diff misses it, and it lives inside
    ``paths``, so the non-path check misses it too. Renaming ``{id}`` to
    ``{slug}`` affects every method on that path and would otherwise be
    dropped silently."""

    other_changes: bool = False
    """True when something outside ``paths`` differs -- schemas, security
    schemes, server list. Not attributed to an endpoint, but still worth
    surfacing rather than dropping."""

    notes: tuple[str, ...] = field(default=())

    @property
    def has_drift(self) -> bool:
        return bool(
            self.added or self.removed or self.changed or self.changed_shared or self.other_changes
        )

    def summary(self) -> str:
        """One line, suitable for a log or an issue title."""
        if not self.has_drift:
            return "No drift: the pinned spec matches master."
        parts = []
        if self.added:
            parts.append(f"{len(self.added)} added")
        if self.removed:
            parts.append(f"{len(self.removed)} removed")
        if self.changed:
            parts.append(f"{len(self.changed)} changed")
        if self.changed_shared:
            parts.append(f"{len(self.changed_shared)} with changed shared parameters")
        if self.other_changes:
            parts.append("non-path changes")
        return "API drift: " + ", ".join(parts)


def _operations(spec: dict[str, Any]) -> dict[str, Any]:
    """Map ``"METHOD /path"`` to that operation's definition.

    Path-item keys that are not HTTP methods (``parameters``, ``summary``,
    ``$ref``) are metadata and are skipped, so a change to shared path
    parameters surfaces through the path item rather than as a phantom
    operation.
    """
    ops: dict[str, Any] = {}
    for path, item in (spec.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method, definition in item.items():
            if method.lower() in _HTTP_METHODS:
                ops[f"{method.upper()} {path}"] = definition
    return ops


def _shared(item: Any) -> dict[str, Any]:
    """Path-item keys that are not operations -- ``parameters``, ``summary``."""
    if not isinstance(item, dict):
        return {}
    return {k: v for k, v in item.items() if k.lower() not in _HTTP_METHODS}


def compare(pinned: dict[str, Any], candidate: dict[str, Any]) -> OpenApiDrift:
    """Compare ``candidate`` (typically ``master``) against ``pinned``."""
    before = _operations(pinned)
    after = _operations(candidate)

    added = tuple(sorted(set(after) - set(before)))
    removed = tuple(sorted(set(before) - set(after)))
    changed = tuple(sorted(key for key in set(before) & set(after) if before[key] != after[key]))

    before_paths = pinned.get("paths") or {}
    after_paths = candidate.get("paths") or {}
    changed_shared = tuple(
        sorted(
            path
            for path in set(before_paths) & set(after_paths)
            if _shared(before_paths[path]) != _shared(after_paths[path])
        )
    )

    # Anything outside paths: component schemas, security, servers. Compared
    # wholesale because attributing a schema change to the endpoints that
    # reference it needs $ref resolution, which is more machinery than a
    # weekly alert warrants.
    other_changes = any(
        pinned.get(key) != candidate.get(key) for key in (set(pinned) | set(candidate)) - {"paths"}
    )

    notes = []
    if changed_shared:
        notes.append(
            "Shared path parameters changed. These apply to every method on "
            "the path, so more endpoints may be affected than the count suggests."
        )
    if other_changes and not (added or removed or changed or changed_shared):
        notes.append(
            "Changes are outside `paths` -- component schemas, security, or "
            "servers. These can still alter request and response shapes that "
            "documented endpoints reference."
        )
    if changed and not (added or removed):
        notes.append(
            "No endpoints were added or removed; existing definitions changed. "
            "Published prose describing these endpoints may now be wrong."
        )

    return OpenApiDrift(
        added=added,
        removed=removed,
        changed=changed,
        changed_shared=changed_shared,
        other_changes=other_changes,
        notes=tuple(notes),
    )


def to_markdown(drift: OpenApiDrift, *, pinned_ref: str, candidate_ref: str) -> str:
    """Render a drift report for a GitHub issue body."""
    if not drift.has_drift:
        return f"The pinned spec (`{pinned_ref}`) matches `{candidate_ref}`. No API drift."

    lines = [
        f"`server/swagger/openapi.json` differs between the pinned "
        f"`{pinned_ref}` and `{candidate_ref}`.",
        "",
    ]

    def section(title: str, items: tuple[str, ...]) -> None:
        if items:
            lines.append(f"**{title}**")
            lines.append("")
            lines.extend(f"- `{item}`" for item in items)
            lines.append("")

    section("Added endpoints", drift.added)
    section("Removed endpoints", drift.removed)
    section("Changed definitions", drift.changed)
    section("Changed shared path parameters", drift.changed_shared)

    if drift.other_changes:
        lines.append("**Changes outside `paths`** — component schemas, security, or servers.\n")

    for note in drift.notes:
        lines.append(f"> {note}")
        lines.append("")

    lines.append(
        "This reports drift on the upstream default branch. It is not a "
        "request to bump the pin — the pin follows releases (FR-1). It is a "
        "heads-up that published prose may be describing behaviour that has "
        "since changed, and that the next release will carry it."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Compare two spec files and print a report.

    Exit code is the signal, so a caller does not have to parse the output:
    ``0`` no drift, ``1`` drift found. Anything else is a real error.
    """
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pinned", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--pinned-ref", default="pinned")
    parser.add_argument("--candidate-ref", default="master")
    args = parser.parse_args(argv)

    drift = compare(
        json.loads(args.pinned.read_text(encoding="utf-8")),
        json.loads(args.candidate.read_text(encoding="utf-8")),
    )
    print(to_markdown(drift, pinned_ref=args.pinned_ref, candidate_ref=args.candidate_ref))
    return 1 if drift.has_drift else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
