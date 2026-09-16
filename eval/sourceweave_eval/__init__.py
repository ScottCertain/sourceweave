"""SourceWeave evaluation harness.

Scores generated output for style-guide adherence (PRD FR-11) and factual
accuracy against pinned source (PRD FR-12), and aggregates summarized scores
into quality trends (PRD FR-15).

Evaluation runs on a different model tier than generation -- see
docs/decisions/0002-model-access-via-claude-subscription.md.
"""

__version__ = "0.1.0"
