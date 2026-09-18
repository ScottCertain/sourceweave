"""Tests for OpenAPI drift detection.

The case that motivates this module is the third one: same endpoints on both
sides, definitions changed. Measured against the real v1.16.1 pin and
``master``, that was the only drift present -- a comparison that looked at
endpoint names alone would have reported nothing.
"""

from sourceweave_pipeline.openapi_drift import compare


def _spec(paths):
    return {"openapi": "3.0.0", "info": {"title": "t", "version": "1"}, "paths": paths}


class TestNoDrift:
    def test_identical_specs_report_nothing(self):
        spec = _spec({"/a": {"get": {"summary": "a"}}})
        drift = compare(spec, spec)
        assert not drift.has_drift
        assert drift.summary() == "No drift: the pinned spec matches master."

    def test_empty_specs_are_equal(self):
        assert not compare(_spec({}), _spec({})).has_drift


class TestEndpointSetChanges:
    def test_added_endpoint(self):
        before = _spec({"/a": {"get": {}}})
        after = _spec({"/a": {"get": {}}, "/b": {"post": {}}})
        drift = compare(before, after)
        assert drift.added == ("POST /b",)
        assert not drift.removed and not drift.changed

    def test_removed_endpoint(self):
        before = _spec({"/a": {"get": {}}, "/b": {"post": {}}})
        after = _spec({"/a": {"get": {}}})
        drift = compare(before, after)
        assert drift.removed == ("POST /b",)

    def test_method_added_to_existing_path_is_an_addition(self):
        before = _spec({"/a": {"get": {}}})
        after = _spec({"/a": {"get": {}, "delete": {}}})
        drift = compare(before, after)
        assert drift.added == ("DELETE /a",)
        assert not drift.changed


class TestChangedDefinitions:
    """The case a naive endpoint-name comparison misses entirely."""

    def test_same_endpoints_changed_body_is_drift(self):
        before = _spec({"/a": {"get": {"summary": "old"}}})
        after = _spec({"/a": {"get": {"summary": "new"}}})
        drift = compare(before, after)
        assert drift.changed == ("GET /a",)
        assert not drift.added and not drift.removed
        assert drift.has_drift

    def test_changed_only_carries_a_warning_note(self):
        before = _spec({"/a": {"get": {"summary": "old"}}})
        after = _spec({"/a": {"get": {"summary": "new"}}})
        notes = " ".join(compare(before, after).notes)
        assert "may now be wrong" in notes


class TestNonPathChanges:
    def test_component_schema_change_is_drift(self):
        before = _spec({"/a": {"get": {}}}) | {"components": {"schemas": {"S": {"x": 1}}}}
        after = _spec({"/a": {"get": {}}}) | {"components": {"schemas": {"S": {"x": 2}}}}
        drift = compare(before, after)
        assert drift.other_changes
        assert drift.has_drift
        assert not drift.added and not drift.removed and not drift.changed

    def test_non_path_change_carries_an_explanatory_note(self):
        before = _spec({}) | {"components": {"schemas": {"S": {"x": 1}}}}
        after = _spec({}) | {"components": {"schemas": {"S": {"x": 2}}}}
        assert "outside `paths`" in " ".join(compare(before, after).notes)


class TestPathItemMetadata:
    def test_shared_parameters_are_not_treated_as_an_operation(self):
        """`parameters` sits beside methods in a path item but is not one.

        Counting it as an operation would invent a `PARAMETERS /a` endpoint.
        """
        spec = _spec({"/a": {"parameters": [{"name": "id"}], "get": {}}})
        drift = compare(spec, spec)
        assert not drift.has_drift

    def test_shared_parameter_change_surfaces_as_a_changed_path(self):
        before = _spec({"/a": {"parameters": [{"name": "id"}], "get": {}}})
        after = _spec({"/a": {"parameters": [{"name": "slug"}], "get": {}}})
        drift = compare(before, after)
        # Not an operation-level change, so it lands in the non-path bucket
        # rather than being silently dropped.
        assert drift.has_drift


class TestSummary:
    def test_summary_counts_each_category(self):
        before = _spec({"/a": {"get": {}}, "/gone": {"get": {}}})
        after = _spec({"/a": {"get": {"summary": "x"}}, "/new": {"get": {}}})
        summary = compare(before, after).summary()
        assert "1 added" in summary
        assert "1 removed" in summary
        assert "1 changed" in summary
