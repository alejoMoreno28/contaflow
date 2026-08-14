"""Lectura y construcción segura de filas del catálogo Yamaha."""

from __future__ import annotations

from datetime import date
from typing import Iterable, Sequence

from yamaha_rules import (
    DESCONTABLE,
    YamahaRuleError,
    calcular_cta_inv,
    enrich_catalog_with_known_oils,
    normalize_product_code,
    normalize_reference,
    product_line_group,
    resolve_tax_treatment,
)


def _value(row: Sequence[object], index: int) -> str:
    return str(row[index]).strip() if len(row) > index and row[index] is not None else ""


def parse_inventory_rows(
    rows: Iterable[Sequence[object]],
) -> dict[str, dict[str, object]]:
    catalog: dict[str, dict[str, object]] = {}

    for row in rows:
        reference = normalize_reference(_value(row, 1))
        if not reference or reference.upper() == "REFERENCIA":
            continue
        product = _value(row, 2)
        if product.startswith("'"):
            product = product[1:].strip()
        catalog[reference] = {
            "producto": product,
            "descripcion": _value(row, 3),
            "cta_inv": _value(row, 4),
            "linea": _value(row, 6),
            "grupo": _value(row, 7),
            "tratamiento_iva": _value(row, 8),
        }

    return enrich_catalog_with_known_oils(catalog)


def sheet_line_group(product: object) -> tuple[str, str]:
    line, group = product_line_group(product)
    return line, f"{int(group):03d}"


def build_catalog_row(
    reference: object,
    product: object,
    description: object,
    tax_treatment: object,
    *,
    creation_date: str | None = None,
) -> list[str]:
    clean_reference = normalize_reference(reference)
    if not clean_reference:
        raise YamahaRuleError("La referencia no puede estar vacia.")

    clean_product = normalize_product_code(product)
    account = calcular_cta_inv(clean_product)
    treatment = resolve_tax_treatment(
        tax_treatment,
        clean_reference,
        clean_product,
    )
    if treatment is None:
        raise YamahaRuleError(
            f"La referencia {clean_reference} requiere definir su tratamiento de IVA."
        )
    if clean_product.startswith("002") and treatment != DESCONTABLE:
        raise YamahaRuleError(
            "Los repuestos 002 deben conservar tratamiento de IVA descontable."
        )

    line, group = sheet_line_group(clean_product)
    return [
        "",
        clean_reference,
        clean_product,
        str(description).strip() if description is not None else "",
        account,
        creation_date or date.today().strftime("%Y-%m-%d"),
        line,
        group,
        treatment,
    ]
