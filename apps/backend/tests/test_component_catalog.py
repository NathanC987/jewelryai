from app.services.component_catalog import component_catalog


def test_component_catalog_manifest_loads() -> None:
    assert component_catalog.schema_version >= 1
    assert component_catalog.catalog_name
    assert len(component_catalog.all_components()) >= 8


def test_component_catalog_has_demo_approved_baseline() -> None:
    approved = [c for c in component_catalog.all_components() if c.status == "approved"]
    approved_ids = {c.id for c in approved}

    assert "band.classic" in approved_ids
    assert "setting.solitaire" in approved_ids
    assert "style.cathedral_arms" in approved_ids


def test_component_catalog_audit_summary_shape() -> None:
    summary = component_catalog.audit()

    assert summary["total_components"] >= 8
    assert "status_counts" in summary
    assert "source_type_counts" in summary
    assert "missing_files" in summary
