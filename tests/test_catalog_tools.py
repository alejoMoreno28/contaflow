import os
import sys

import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "contaflow-api"))
)

from catalog_tools import (
    CatalogUpdateError,
    calcular_cta_inv,
    find_reference_row,
    normalize_product_code,
    update_reference_product,
)
from yamaha_rules import DESCONTABLE, IVA_MAYOR_COSTO


class FakeWorksheet:
    def __init__(self, values):
        self._values = values
        self.batch_updates = []

    def get_all_values(self):
        return self._values

    def batch_update(self, updates, value_input_option=None):
        self.batch_updates.append(
            {"updates": updates, "value_input_option": value_input_option}
        )


def test_normalize_product_code_accepts_sheet_apostrophe_and_spaces():
    assert normalize_product_code(" '0020077000625 ") == "0020077000625"


def test_normalize_product_code_rejects_non_13_digit_values():
    with pytest.raises(CatalogUpdateError, match="13 digitos"):
        normalize_product_code("002007700062")

    with pytest.raises(CatalogUpdateError, match="13 digitos"):
        normalize_product_code("00200770006AB")


def test_calcular_cta_inv_uses_confirmed_siigo_rule():
    assert calcular_cta_inv("0020077000625") == "1435010277"
    assert calcular_cta_inv("0020077000628") == "1435010277"
    assert calcular_cta_inv("0030001000122") == "1435020101"


def test_find_reference_row_uses_column_b_after_header_rows():
    rows = [
        ["", "REFERENCIA", "PRODUCTO", "DESCRIPCION", "CTA-INV"],
        ["", "", "", "", ""],
        ["", "BBKH18001100", "'0020077000628", "DESCRIPCION", "1435010277"],
    ]

    found = find_reference_row(rows, " BBKH18001100 ")

    assert found is not None
    assert found.row_number == 3
    assert found.referencia == "BBKH18001100"
    assert found.producto == "0020077000628"
    assert found.cta_inv == "1435010277"


def test_update_reference_product_updates_product_account_tax_metadata_and_date():
    worksheet = FakeWorksheet(
        [
            ["", "REFERENCIA", "PRODUCTO", "DESCRIPCION", "CTA-INV", "FECHA"],
            ["", "", "", "", "", ""],
            ["", "BBKH18001100", "'0020077000628", "DESCRIPCION", "1435010277", ""],
        ]
    )

    result = update_reference_product(
        worksheet,
        referencia="BBKH18001100",
        nuevo_producto="0020077000625",
        fecha="2026-04-29",
    )

    assert result.row_number == 3
    assert result.old_producto == "0020077000628"
    assert result.new_producto == "0020077000625"
    assert result.old_cta_inv == "1435010277"
    assert result.new_cta_inv == "1435010277"
    assert worksheet.batch_updates == [
        {
            "value_input_option": "USER_ENTERED",
            "updates": [
                {"range": "C3", "values": [["'0020077000625"]]},
                {"range": "E3", "values": [["1435010277"]]},
                {"range": "F3", "values": [["2026-04-29"]]},
                {"range": "G3", "values": [["002"]]},
                {"range": "H3", "values": [["077"]]},
                {"range": "I3", "values": [[DESCONTABLE]]},
            ],
        }
    ]


def test_update_reference_product_requires_and_writes_003_tax_treatment():
    worksheet = FakeWorksheet(
        [
            ["", "REFERENCIA", "PRODUCTO", "DESCRIPCION", "CTA-INV", "FECHA"],
            ["", "NEW-OIL", "'0020001000001", "ACEITE", "1435010201", ""],
        ]
    )

    with pytest.raises(CatalogUpdateError, match="tratamiento de IVA"):
        update_reference_product(
            worksheet,
            referencia="NEW-OIL",
            nuevo_producto="0030001000999",
            fecha="2026-08-14",
        )

    result = update_reference_product(
        worksheet,
        referencia="NEW-OIL",
        nuevo_producto="0030001000999",
        tratamiento_iva=IVA_MAYOR_COSTO,
        fecha="2026-08-14",
    )

    assert result.new_cta_inv == "1435020101"
    assert result.new_tax_treatment == IVA_MAYOR_COSTO
    assert worksheet.batch_updates[-1]["updates"][-3:] == [
        {"range": "G2", "values": [["003"]]},
        {"range": "H2", "values": [["001"]]},
        {"range": "I2", "values": [[IVA_MAYOR_COSTO]]},
    ]


def test_update_reference_product_fails_when_reference_is_missing():
    worksheet = FakeWorksheet(
        [
            ["", "REFERENCIA", "PRODUCTO", "DESCRIPCION", "CTA-INV", "FECHA"],
            ["", "", "", "", "", ""],
        ]
    )

    with pytest.raises(CatalogUpdateError, match="no existe"):
        update_reference_product(
            worksheet,
            referencia="BBKH18001100",
            nuevo_producto="0020077000625",
            fecha="2026-04-29",
        )


def test_update_reference_product_fails_when_reference_is_duplicated():
    worksheet = FakeWorksheet(
        [
            ["", "REFERENCIA", "PRODUCTO", "DESCRIPCION", "CTA-INV", "FECHA"],
            ["", "", "", "", "", ""],
            ["", "BBKH18001100", "'0020077000628", "DESCRIPCION 1", "1435010277", ""],
            ["", "BBKH18001100", "'0020077000625", "DESCRIPCION 2", "1435010277", ""],
        ]
    )

    with pytest.raises(CatalogUpdateError, match="duplicada"):
        update_reference_product(
            worksheet,
            referencia="BBKH18001100",
            nuevo_producto="0020077000625",
            fecha="2026-04-29",
        )
