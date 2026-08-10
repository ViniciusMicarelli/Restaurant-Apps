"""Testes estruturais dos modelos base `BaseDBModel` e `TenantAwareModel`."""

from restaurant_database.base import TenantAwareModel


def test_tenant_aware_model_is_abstract_and_not_directly_mapped() -> None:
    assert TenantAwareModel.__dict__.get("__abstract__") is True


def test_sample_widget_declares_all_expected_base_columns(sample_widget_model) -> None:
    columns = sample_widget_model.__table__.columns

    for expected_column in (
        "id",
        "tenant_id",
        "created_at",
        "updated_at",
        "deleted_at",
        "version_id",
    ):
        assert expected_column in columns, f"coluna '{expected_column}' ausente no modelo base"


def test_version_id_column_is_wired_as_the_optimistic_lock_column(sample_widget_model) -> None:
    mapper = sample_widget_model.__mapper__
    assert mapper.version_id_col is not None
    assert mapper.version_id_col.name == "version_id"


def test_tenant_id_column_is_indexed_and_not_nullable(sample_widget_model) -> None:
    tenant_id_column = sample_widget_model.__table__.columns["tenant_id"]
    assert tenant_id_column.nullable is False
    assert tenant_id_column.index is True
