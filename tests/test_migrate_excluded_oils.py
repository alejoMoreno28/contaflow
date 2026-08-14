from pathlib import Path

import pytest

from scripts.migrate_excluded_oils import (
    MigrationConflict,
    apply_migration,
    plan_migration,
)
from yamaha_rules import EXCLUDED_OILS, IVA_MAYOR_COSTO


def _sheet_with_existing(reference, product, account="1435010201"):
    return [
        ["", "REFERENCIA", "PRODUCTO", "DESCRIPCION", "CTA-INV", "FECHA", "LINEA", "GRUPO"],
        [],
        [],
        [],
        ["INDICATIVO", "REFERENCIA", "PRODUCTO", "DESCRIPCION", "CTA-INV", "FECHA", "LINEA", "GRUPO"],
        ["1", reference, product, "DESCRIPCION EXISTENTE", account, "2026-03-17", "003", "001"],
    ]


def test_plan_updates_existing_oil_and_adds_only_missing_approved_references():
    reference = "90793AV50400"
    product = EXCLUDED_OILS[reference].producto

    plan = plan_migration(
        _sheet_with_existing(reference, product),
        creation_date="2026-08-14",
    )

    assert plan.conflicts == []
    assert len(plan.updates) == 1
    assert plan.updates[0].row_number == 6
    assert plan.updates[0].values == {
        "E": "1435020101",
        "G": "003",
        "H": "001",
        "I": IVA_MAYOR_COSTO,
    }
    assert len(plan.additions) == len(EXCLUDED_OILS) - 1
    assert {row[1] for row in plan.additions} == set(EXCLUDED_OILS) - {reference}
    assert plan.additions[0][2].startswith("0030001")


def test_plan_rejects_approved_reference_with_conflicting_product():
    rows = _sheet_with_existing("90793AV50400", "0030001000999")

    plan = plan_migration(rows, creation_date="2026-08-14")

    assert len(plan.conflicts) == 1
    assert "90793AV50400" in plan.conflicts[0]
    assert plan.updates == []
    assert plan.additions == []


def test_plan_rejects_duplicate_approved_reference():
    reference = "90793AV50400"
    product = EXCLUDED_OILS[reference].producto
    rows = _sheet_with_existing(reference, product)
    rows.append(["2", reference, product, "DUPLICADA", "1435020101"])

    plan = plan_migration(rows, creation_date="2026-08-14")

    assert len(plan.conflicts) == 1
    assert "duplicada" in plan.conflicts[0].lower()


class FakeWorksheet:
    def __init__(self, rows):
        self.rows = [list(row) for row in rows]
        self.batch_updates = []
        self.appended = []

    def get_all_values(self):
        return [list(row) for row in self.rows]

    def batch_update(self, updates, value_input_option=None):
        self.batch_updates.extend(updates)
        self.value_input_option = value_input_option

    def append_rows(self, rows, value_input_option=None):
        self.appended.extend(rows)
        self.value_input_option = value_input_option


def test_apply_migration_is_dry_run_by_default(tmp_path: Path):
    reference = "90793AV50400"
    worksheet = FakeWorksheet(
        _sheet_with_existing(reference, EXCLUDED_OILS[reference].producto)
    )
    plan = plan_migration(worksheet.get_all_values(), creation_date="2026-08-14")

    result = apply_migration(
        worksheet,
        plan,
        apply=False,
        backup_dir=tmp_path,
        timestamp="20260814-120000",
    )

    assert result.backup_json is None
    assert result.backup_csv is None
    assert worksheet.batch_updates == []
    assert worksheet.appended == []


def test_apply_migration_backs_up_before_writes(tmp_path: Path):
    reference = "90793AV50400"
    worksheet = FakeWorksheet(
        _sheet_with_existing(reference, EXCLUDED_OILS[reference].producto)
    )
    plan = plan_migration(worksheet.get_all_values(), creation_date="2026-08-14")

    result = apply_migration(
        worksheet,
        plan,
        apply=True,
        backup_dir=tmp_path,
        timestamp="20260814-120000",
    )

    assert result.backup_json and result.backup_json.exists()
    assert result.backup_csv and result.backup_csv.exists()
    assert {update["range"] for update in worksheet.batch_updates} >= {
        "I1",
        "I5",
        "E6",
        "G6",
        "H6",
        "I6",
    }
    assert len(worksheet.appended) == len(EXCLUDED_OILS) - 1
    assert worksheet.value_input_option == "RAW"


def test_apply_migration_refuses_conflicts(tmp_path: Path):
    worksheet = FakeWorksheet(
        _sheet_with_existing("90793AV50400", "0030001000999")
    )
    plan = plan_migration(worksheet.get_all_values(), creation_date="2026-08-14")

    with pytest.raises(MigrationConflict):
        apply_migration(
            worksheet,
            plan,
            apply=True,
            backup_dir=tmp_path,
            timestamp="20260814-120000",
        )

    assert worksheet.batch_updates == []
    assert worksheet.appended == []
