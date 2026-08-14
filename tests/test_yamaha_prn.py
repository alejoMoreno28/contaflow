from decimal import Decimal

import pytest

from yamaha_prn import PrnValidationError, build_accounting_plan, generar_prn_lines
from yamaha_rules import DESCONTABLE, IVA_MAYOR_COSTO


STORES = {"GIRARDOT": {"cc": 95, "doc": 240}}

EXPECTED_002 = (
    "P2400000075030400001000089091691100014350102100020010000001202403240095000YAMALUBE                                          D000000005210000000000000000000000000000000095000000000000200000 0000000000000000000000000000000\r\n"
    "P2400000075030400002000089091691100022050100000000000000000202403240095000INCOLMOTOS SAS                                    C000000006199900000000000000000000000000000095000000000000000000P2400000075030400120240408000000\r\n"
    "P2400000075030400003000089091691100024080201000000000000000202403240095000INCOLMOTOS SAS                                    D000000000989900000000000000000000000000000095000000000000100000 0000000000000000000000000000000\r\n"
)


def _invoice(*, subtotal, iva_total, items, number="CPFE-790425"):
    return {
        "numero_factura": number,
        "fecha": "2026-06-19",
        "ciudad": "IBAGUE",
        "direccion_entrega": "CR 5 20 39 B 1 CARMEN",
        "subtotal": subtotal,
        "iva_total": iva_total,
        "fecha_vto": "20260719",
        "items": items,
    }


def _item(reference, value, quantity=1, description="ITEM"):
    return {
        "referencia": reference,
        "descripcion": description,
        "cantidad": quantity,
        "valor_total": value,
    }


def _line_account(line):
    return line[36:46]


def _line_product(line):
    return line[46:59]


def _line_value(line):
    return Decimal(line[125:140]) / 100


def test_002_prn_remains_byte_for_byte_identical():
    invoice = {
        "numero_factura": "CPFE-750304",
        "fecha": "2024-03-24",
        "ciudad": "GIRARDOT",
        "direccion_entrega": "CRA 50 12 34",
        "subtotal": 52100.0,
        "iva_total": 9899.0,
        "fecha_vto": "20240408",
        "items": [_item("90793AQ82100", 52100.0, 2, "YAMALUBE")],
    }
    catalog = {
        "90793AQ82100": {
            "producto": "0020010000001",
            "cta_inv": "1435010210",
        }
    }

    content = "\r\n".join(generar_prn_lines(invoice, catalog, STORES)) + "\r\n"

    assert content == EXPECTED_002


def test_invoice_790425_capitalizes_iva_and_omits_deductible_vat():
    invoice = _invoice(
        subtotal=516_307,
        iva_total=98_098,
        items=[
            _item(
                "90793AV50400",
                516_307,
                12,
                "ACEITE FULL SINTETICO 10W40 MA2-1000 CC",
            )
        ],
    )
    catalog = {
        "90793AV50400": {
            "producto": "0030001000122",
            "cta_inv": "1435010201",
        }
    }

    plan = build_accounting_plan(invoice, catalog)
    lines = generar_prn_lines(invoice, catalog, STORES)

    assert plan.item_movements[0].account == "1435020101"
    assert plan.item_movements[0].base == Decimal("516307.00")
    assert plan.item_movements[0].capitalized_vat == Decimal("98098.00")
    assert plan.item_movements[0].amount == Decimal("614405.00")
    assert plan.capitalized_vat == Decimal("98098.00")
    assert plan.deductible_vat == Decimal("0.00")
    assert plan.debit_total == plan.credit_total == Decimal("614405.00")
    assert len(lines) == 2
    assert _line_account(lines[0]) == "1435020101"
    assert _line_product(lines[0]) == "0030001000122"
    assert _line_value(lines[0]) == Decimal("614405.00")
    assert _line_account(lines[1]) == "2205010000"
    assert _line_value(lines[1]) == Decimal("614405.00")


def test_mixed_invoice_capitalizes_only_oil_vat():
    invoice = _invoice(
        subtotal=1_500,
        iva_total=285,
        items=[
            _item("REPUESTO002", 1_000),
            _item("90793AV50400", 500),
        ],
    )
    catalog = {
        "REPUESTO002": {
            "producto": "0020001000001",
            "cta_inv": "1435010201",
        },
        "90793AV50400": {
            "producto": "0030001000122",
            "cta_inv": "1435020101",
            "tratamiento_iva": IVA_MAYOR_COSTO,
        },
    }

    plan = build_accounting_plan(invoice, catalog)
    lines = generar_prn_lines(invoice, catalog, STORES)

    assert [movement.amount for movement in plan.item_movements] == [
        Decimal("1000.00"),
        Decimal("595.00"),
    ]
    assert plan.capitalized_vat == Decimal("95.00")
    assert plan.deductible_vat == Decimal("190.00")
    assert plan.debit_total == plan.credit_total == Decimal("1785.00")
    assert [_line_account(line) for line in lines] == [
        "1435010201",
        "1435020101",
        "2205010000",
        "2408020100",
    ]
    assert _line_value(lines[-1]) == Decimal("190.00")


def test_multiple_oils_put_group_rounding_difference_on_last_item():
    invoice = _invoice(
        subtotal=3,
        iva_total=1,
        items=[
            _item("OIL-A", 1),
            _item("OIL-B", 1),
            _item("OIL-C", 1),
        ],
    )
    catalog = {
        "OIL-A": {
            "producto": "0030001000901",
            "cta_inv": "1435020101",
            "tratamiento_iva": IVA_MAYOR_COSTO,
        },
        "OIL-B": {
            "producto": "0030001000902",
            "cta_inv": "1435020101",
            "tratamiento_iva": IVA_MAYOR_COSTO,
        },
        "OIL-C": {
            "producto": "0030001000903",
            "cta_inv": "1435020101",
            "tratamiento_iva": IVA_MAYOR_COSTO,
        },
    }

    plan = build_accounting_plan(invoice, catalog)

    assert plan.capitalized_vat == Decimal("1.00")
    assert [movement.capitalized_vat for movement in plan.item_movements] == [
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("1.00"),
    ]
    assert plan.deductible_vat == Decimal("0.00")


def test_unknown_003_requires_explicit_tax_treatment():
    invoice = _invoice(
        subtotal=100,
        iva_total=19,
        items=[_item("NEW-OIL", 100)],
    )
    catalog = {
        "NEW-OIL": {
            "producto": "0030001000999",
            "cta_inv": "1435020101",
        }
    }

    with pytest.raises(PrnValidationError, match="tratamiento de IVA"):
        build_accounting_plan(invoice, catalog)


def test_taxable_003_keeps_invoice_vat_deductible():
    invoice = _invoice(
        subtotal=100,
        iva_total=19,
        items=[_item("TAXABLE-OIL", 100)],
    )
    catalog = {
        "TAXABLE-OIL": {
            "producto": "0030001000998",
            "cta_inv": "1435020101",
            "tratamiento_iva": DESCONTABLE,
        }
    }

    plan = build_accounting_plan(invoice, catalog)

    assert plan.item_movements[0].amount == Decimal("100.00")
    assert plan.capitalized_vat == Decimal("0.00")
    assert plan.deductible_vat == Decimal("19.00")


def test_insufficient_invoice_vat_blocks_generation():
    invoice = _invoice(
        subtotal=1_000,
        iva_total=100,
        items=[_item("90793AV50400", 1_000)],
    )
    catalog = {
        "90793AV50400": {
            "producto": "0030001000122",
            "cta_inv": "1435020101",
        }
    }

    with pytest.raises(PrnValidationError, match="supera el IVA total"):
        build_accounting_plan(invoice, catalog)


def test_subtotal_mismatch_blocks_an_unbalanced_prn():
    invoice = _invoice(
        subtotal=101,
        iva_total=19,
        items=[_item("REPUESTO002", 100)],
    )
    catalog = {
        "REPUESTO002": {
            "producto": "0020001000001",
            "cta_inv": "1435010201",
        }
    }

    with pytest.raises(PrnValidationError, match="subtotal"):
        build_accounting_plan(invoice, catalog)
