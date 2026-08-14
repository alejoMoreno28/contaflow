import pytest

from yamaha_catalog import build_catalog_row, parse_inventory_rows
from yamaha_rules import DESCONTABLE, IVA_MAYOR_COSTO, YamahaRuleError


def test_inventory_rows_read_treatment_from_column_i():
    catalog = parse_inventory_rows(
        [
            ["", "REFERENCIA", "PRODUCTO", "DESCRIPCION", "CTA-INV"],
            [
                "",
                "TAXABLE-OIL",
                "'0030001000998",
                "ACEITE GRAVADO",
                "1435020101",
                "2026-08-14",
                "003",
                "001",
                DESCONTABLE,
            ],
        ]
    )

    assert catalog["TAXABLE-OIL"] == {
        "producto": "0030001000998",
        "descripcion": "ACEITE GRAVADO",
        "cta_inv": "1435020101",
        "linea": "003",
        "grupo": "001",
        "tratamiento_iva": DESCONTABLE,
    }


def test_old_or_offline_catalog_is_protected_by_approved_oil_master():
    catalog = parse_inventory_rows(
        [
            [
                "",
                "90793AV50400",
                "'0030001000122",
                "ACEITE FULL SINTETICO",
                "1435010201",
            ]
        ]
    )

    assert catalog["90793AV50400"]["cta_inv"] == "1435020101"
    assert catalog["90793AV50400"]["tratamiento_iva"] == IVA_MAYOR_COSTO
    assert catalog["90793AV50100"]["producto"] == "0030001000116"


def test_unknown_003_remains_unclassified_until_user_answers():
    catalog = parse_inventory_rows(
        [["", "NEW-OIL", "'0030001000999", "NUEVO", "1435020101", "", "003", "001", ""]]
    )

    assert catalog["NEW-OIL"]["tratamiento_iva"] == ""


def test_build_catalog_row_requires_treatment_for_new_003():
    with pytest.raises(YamahaRuleError, match="tratamiento de IVA"):
        build_catalog_row("NEW-OIL", "0030001000999", "NUEVO", "")

    row = build_catalog_row(
        "NEW-OIL",
        "0030001000999",
        "NUEVO",
        IVA_MAYOR_COSTO,
        creation_date="2026-08-14",
    )
    assert row == [
        "",
        "NEW-OIL",
        "'0030001000999",
        "NUEVO",
        "1435020101",
        "2026-08-14",
        "003",
        "001",
        IVA_MAYOR_COSTO,
    ]


def test_build_catalog_row_preserves_002_rule():
    row = build_catalog_row(
        "REPUESTO",
        "0020077000625",
        "REPUESTO NORMAL",
        "",
        creation_date="2026-08-14",
    )

    assert row[4:] == ["1435010277", "2026-08-14", "002", "077", DESCONTABLE]
