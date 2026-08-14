from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Sequence

from yamaha_catalog import build_catalog_row
from yamaha_rules import (
    YamahaRuleError,
    calcular_cta_inv as _calcular_cta_inv,
    normalize_product_code as _normalize_product_code,
)


class CatalogUpdateError(ValueError):
    """Raised when a catalog correction cannot be applied safely."""


@dataclass(frozen=True)
class CatalogRow:
    row_number: int
    referencia: str
    producto: str
    descripcion: str
    cta_inv: str
    tax_treatment: str


@dataclass(frozen=True)
class CatalogUpdateResult:
    row_number: int
    referencia: str
    old_producto: str
    new_producto: str
    old_cta_inv: str
    new_cta_inv: str
    old_tax_treatment: str
    new_tax_treatment: str


def clean_sheet_text(value: object) -> str:
    return str(value).strip() if value is not None else ""


def normalize_reference(value: object) -> str:
    return clean_sheet_text(value)


def normalize_product_code(value: object) -> str:
    try:
        return _normalize_product_code(value)
    except YamahaRuleError as exc:
        raise CatalogUpdateError(str(exc)) from exc


def calcular_cta_inv(codigo_producto: str) -> str:
    try:
        return _calcular_cta_inv(codigo_producto)
    except YamahaRuleError as exc:
        raise CatalogUpdateError("No se pudo calcular la cuenta de inventario.") from exc


def _row_value(row: Sequence[object], index: int) -> str:
    return clean_sheet_text(row[index]) if len(row) > index else ""


def find_reference_row(rows: Sequence[Sequence[object]], referencia: object) -> CatalogRow | None:
    target = normalize_reference(referencia)
    matches: list[CatalogRow] = []

    for row_number, row in enumerate(rows, start=1):
        row_ref = normalize_reference(_row_value(row, 1))
        if row_ref != target:
            continue
        matches.append(
            CatalogRow(
                row_number=row_number,
                referencia=row_ref,
                producto=normalize_product_code(_row_value(row, 2)),
                descripcion=_row_value(row, 3),
                cta_inv=_row_value(row, 4),
                tax_treatment=_row_value(row, 8),
            )
        )

    if len(matches) > 1:
        raise CatalogUpdateError(
            f"La referencia {target} esta duplicada en el catalogo. Revisala manualmente."
        )

    return matches[0] if matches else None


def update_reference_product(
    worksheet,
    *,
    referencia: object,
    nuevo_producto: object,
    tratamiento_iva: object = "",
    fecha: str | None = None,
) -> CatalogUpdateResult:
    ref = normalize_reference(referencia)
    product_code = normalize_product_code(nuevo_producto)
    correction_date = fecha or date.today().strftime("%Y-%m-%d")

    found = find_reference_row(worksheet.get_all_values(), ref)
    if found is None:
        raise CatalogUpdateError(f"La referencia {ref} no existe en el catalogo.")

    try:
        new_row = build_catalog_row(
            ref,
            product_code,
            found.descripcion,
            tratamiento_iva,
            creation_date=correction_date,
        )
    except YamahaRuleError as exc:
        raise CatalogUpdateError(str(exc)) from exc
    new_cta_inv = new_row[4]
    new_tax_treatment = new_row[8]

    worksheet.batch_update(
        [
            {"range": f"C{found.row_number}", "values": [[f"'{product_code}"]]},
            {"range": f"E{found.row_number}", "values": [[new_cta_inv]]},
            {"range": f"F{found.row_number}", "values": [[correction_date]]},
            {"range": f"G{found.row_number}", "values": [[new_row[6]]]},
            {"range": f"H{found.row_number}", "values": [[new_row[7]]]},
            {"range": f"I{found.row_number}", "values": [[new_tax_treatment]]},
        ],
        value_input_option="USER_ENTERED",
    )

    return CatalogUpdateResult(
        row_number=found.row_number,
        referencia=found.referencia,
        old_producto=found.producto,
        new_producto=product_code,
        old_cta_inv=found.cta_inv,
        new_cta_inv=new_cta_inv,
        old_tax_treatment=found.tax_treatment,
        new_tax_treatment=new_tax_treatment,
    )
