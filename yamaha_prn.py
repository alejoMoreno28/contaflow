"""Planeación contable y serialización PRN para facturas Yamaha."""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, ROUND_HALF_UP
import unicodedata
from typing import Mapping

from yamaha_rules import (
    IVA_MAYOR_COSTO,
    YamahaRuleError,
    calcular_cta_inv,
    enrich_catalog_with_known_oils,
    normalize_product_code,
    resolve_tax_treatment,
)


NIT_INCOLMOTOS = "890916911"
CENT = Decimal("0.01")
PESO = Decimal("1")
IVA_RATE = Decimal("0.19")


class PrnValidationError(ValueError):
    """Impide generar un PRN con clasificación o balance inseguros."""


@dataclass(frozen=True)
class ItemMovement:
    reference: str
    product: str
    account: str
    description: str
    quantity: Decimal
    treatment: str
    base: Decimal
    capitalized_vat: Decimal
    amount: Decimal


@dataclass(frozen=True)
class AccountingPlan:
    item_movements: tuple[ItemMovement, ...]
    subtotal: Decimal
    invoice_vat: Decimal
    capitalized_vat: Decimal
    deductible_vat: Decimal
    credit_total: Decimal
    debit_total: Decimal


def _decimal(value: object, *, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise PrnValidationError(f"El campo {field} no es un numero valido.") from exc
    if not result.is_finite():
        raise PrnValidationError(f"El campo {field} no es un numero finito.")
    return result


def _money(value: object, *, field: str) -> Decimal:
    return _decimal(value, field=field).quantize(CENT, rounding=ROUND_HALF_UP)


def _scaled_integer(value: object, scale: int, *, field: str) -> int:
    number = _decimal(value, field=field)
    return int((number * scale).quantize(PESO, rounding=ROUND_HALF_EVEN))


def build_accounting_plan(
    factura_data: Mapping[str, object],
    inv: Mapping[str, Mapping[str, object]],
) -> AccountingPlan:
    try:
        catalog = enrich_catalog_with_known_oils(inv)
    except YamahaRuleError as exc:
        raise PrnValidationError(str(exc)) from exc

    subtotal = _money(factura_data.get("subtotal", 0), field="subtotal")
    invoice_vat = _money(factura_data.get("iva_total", 0), field="iva_total")
    if subtotal < 0 or invoice_vat < 0:
        raise PrnValidationError("Subtotal e IVA deben ser valores no negativos.")

    raw_items = factura_data.get("items", [])
    if not isinstance(raw_items, list) or not raw_items:
        raise PrnValidationError("La factura no contiene items para generar el PRN.")

    movements: list[ItemMovement] = []
    excluded_indexes: list[int] = []

    for index, raw_item in enumerate(raw_items):
        if not isinstance(raw_item, Mapping):
            raise PrnValidationError(f"El item {index + 1} no tiene una estructura valida.")

        reference = str(raw_item.get("referencia", "")).strip()
        if not reference or reference not in catalog:
            raise PrnValidationError(
                f"La referencia '{reference or '?'}' no existe en el catalogo."
            )

        lookup = catalog[reference]
        try:
            product = normalize_product_code(lookup.get("producto", ""))
            expected_account = calcular_cta_inv(product)
            treatment = resolve_tax_treatment(
                lookup.get("tratamiento_iva", ""),
                reference,
                product,
            )
        except YamahaRuleError as exc:
            raise PrnValidationError(f"Referencia {reference}: {exc}") from exc

        catalog_account = str(lookup.get("cta_inv", "")).strip()
        if catalog_account != expected_account:
            raise PrnValidationError(
                f"La referencia {reference} tiene cuenta {catalog_account or 'vacia'}, "
                f"pero el producto {product} exige {expected_account}."
            )
        if treatment is None:
            raise PrnValidationError(
                f"La referencia {reference} no tiene tratamiento de IVA definido."
            )

        base = _money(raw_item.get("valor_total", 0), field=f"valor_total item {index + 1}")
        quantity = _decimal(raw_item.get("cantidad", 1), field=f"cantidad item {index + 1}")
        if base < 0 or quantity < 0:
            raise PrnValidationError(
                f"La referencia {reference} contiene base o cantidad negativa."
            )

        movement = ItemMovement(
            reference=reference,
            product=product,
            account=expected_account,
            description=str(raw_item.get("descripcion", "")),
            quantity=quantity,
            treatment=treatment,
            base=base,
            capitalized_vat=Decimal("0.00"),
            amount=base,
        )
        movements.append(movement)
        if treatment == IVA_MAYOR_COSTO:
            excluded_indexes.append(index)

    item_subtotal = sum((movement.base for movement in movements), Decimal("0.00"))
    if item_subtotal != subtotal:
        raise PrnValidationError(
            "La suma de items no coincide exactamente con el subtotal: "
            f"items={item_subtotal:.2f}, subtotal={subtotal:.2f}."
        )

    capitalized_vat = Decimal("0.00")
    if excluded_indexes:
        excluded_base = sum(
            (movements[index].base for index in excluded_indexes),
            Decimal("0.00"),
        )
        capitalized_vat = (excluded_base * IVA_RATE).quantize(
            PESO,
            rounding=ROUND_HALF_UP,
        ).quantize(CENT)

        allocated = Decimal("0.00")
        for index in excluded_indexes:
            item_vat = (movements[index].base * IVA_RATE).quantize(
                PESO,
                rounding=ROUND_HALF_UP,
            ).quantize(CENT)
            movements[index] = replace(
                movements[index],
                capitalized_vat=item_vat,
                amount=movements[index].base + item_vat,
            )
            allocated += item_vat

        last_index = excluded_indexes[-1]
        rounding_delta = capitalized_vat - allocated
        if rounding_delta:
            last = movements[last_index]
            movements[last_index] = replace(
                last,
                capitalized_vat=last.capitalized_vat + rounding_delta,
                amount=last.amount + rounding_delta,
            )

    if capitalized_vat > invoice_vat:
        raise PrnValidationError(
            "El IVA calculado para aceites excluidos supera el IVA total de la factura: "
            f"capitalizado={capitalized_vat:.2f}, factura={invoice_vat:.2f}."
        )

    deductible_vat = invoice_vat - capitalized_vat
    credit_total = subtotal + invoice_vat
    debit_total = (
        sum((movement.amount for movement in movements), Decimal("0.00"))
        + deductible_vat
    )
    if debit_total != credit_total:
        raise PrnValidationError(
            "El PRN no balancea: "
            f"debitos={debit_total:.2f}, credito={credit_total:.2f}."
        )

    return AccountingPlan(
        item_movements=tuple(movements),
        subtotal=subtotal,
        invoice_vat=invoice_vat,
        capitalized_vat=capitalized_vat,
        deductible_vat=deductible_vat,
        credit_total=credit_total,
        debit_total=debit_total,
    )


def _normalizar_ciudad(texto: object) -> str:
    normalized = (
        unicodedata.normalize("NFD", str(texto))
        .encode("ascii", "ignore")
        .decode("utf-8")
        .upper()
        .strip()
    )
    if not normalized:
        raise PrnValidationError("La factura no tiene ciudad.")
    return normalized.split()[0]


def _resolver_tienda_ibague(direccion: object) -> tuple[int, int]:
    normalized = (
        unicodedata.normalize("NFD", str(direccion))
        .encode("ascii", "ignore")
        .decode()
        .upper()
    )
    principal = [
        "CR 5", "CRR 5", "CARRERA 5", "CRA 5", "QUINTA",
        "20 39", "20-39", "B 1 CARMEN", "PRINCIPAL",
    ]
    sexta = [
        "CR 6", "CRR 6", "CARRERA 6", "CRA 6", "BELALCAZAR",
        "BRR BELALCAZAR", "SEXTA", "25 40", "25-40",
    ]
    if any(keyword in normalized for keyword in principal):
        return 7, 14
    if any(keyword in normalized for keyword in sexta):
        return 1, 1
    return 1, 1


def _format_item_line(
    *,
    sec: int,
    doc: int,
    num_doc: str,
    fecha: str,
    cc: int,
    cuenta: str,
    producto: str,
    descripcion: str,
    deb_cred: str,
    valor: object,
    cantidad: object,
) -> str:
    description = (
        unicodedata.normalize("NFKD", str(descripcion))
        .encode("ascii", "ignore")
        .decode("utf-8")
        .upper()
    )
    line = (
        "P"
        + str(doc).zfill(3)
        + num_doc.zfill(11)
        + str(sec).zfill(5)
        + NIT_INCOLMOTOS.zfill(13)
        + "000"
        + str(cuenta).ljust(10)[:10]
        + str(producto).ljust(13)[:13]
        + fecha
        + str(cc).zfill(4)
        + "000"
        + description.ljust(50)[:50]
        + deb_cred
        + str(_scaled_integer(valor, 100, field="valor PRN")).zfill(15)
        + "000000000000000"
        + "0000"
        + "0000"
        + "000"
        + str(cc).zfill(4)
        + "000"
        + str(_scaled_integer(cantidad, 100000, field="cantidad PRN")).zfill(15)
        + " "
        + "000"
        + "00000000000"
        + "000"
        + "00000000"
        + "0000"
        + "00"
    )
    if len(line) != 220:
        raise PrnValidationError(
            f"Error interno generando PRN: linea tiene {len(line)} caracteres (esperado 220)."
        )
    return line


def generar_prn_lines(
    factura_data: Mapping[str, object],
    inv: Mapping[str, Mapping[str, object]],
    tiendas: Mapping[str, Mapping[str, object]],
) -> list[str]:
    plan = build_accounting_plan(factura_data, inv)
    ciudad = _normalizar_ciudad(factura_data.get("ciudad", ""))
    if "IBAGU" in ciudad:
        cc, doc = _resolver_tienda_ibague(factura_data.get("direccion_entrega", ""))
    else:
        if ciudad not in tiendas:
            raise PrnValidationError(f"Ciudad '{ciudad}' no encontrada en Excel DATOS.")
        cc = int(tiendas[ciudad]["cc"])
        doc = int(tiendas[ciudad]["doc"])

    num_doc = (
        str(factura_data.get("numero_factura", ""))
        .replace("CPFE-", "")
        .replace("CPFE", "")
        .strip()
    )
    fecha = str(factura_data.get("fecha", "")).replace("-", "")
    if not (num_doc.isdigit() and fecha.isdigit() and len(fecha) == 8):
        raise PrnValidationError("Numero de factura o fecha invalidos para el PRN.")
    raw_due_date = str(factura_data.get("fecha_vto", "")).strip()
    due_date = (
        raw_due_date
        if raw_due_date.isdigit() and len(raw_due_date) == 8
        else "00000000"
    )

    lines: list[str] = []
    sec = 1
    for movement in plan.item_movements:
        lines.append(
            _format_item_line(
                sec=sec,
                doc=doc,
                num_doc=num_doc,
                fecha=fecha,
                cc=cc,
                cuenta=movement.account,
                producto=movement.product,
                descripcion=movement.description,
                deb_cred="D",
                valor=movement.amount,
                cantidad=movement.quantity,
            )
        )
        sec += 1

    cxp_line = (
        "P"
        + str(doc).zfill(3)
        + num_doc.zfill(11)
        + str(sec).zfill(5)
        + NIT_INCOLMOTOS.zfill(13)
        + "000"
        + "2205010000"
        + "0000000000000"
        + fecha
        + str(cc).zfill(4)
        + "000"
        + "INCOLMOTOS SAS".ljust(50)[:50]
        + "C"
        + str(_scaled_integer(plan.credit_total, 100, field="total factura")).zfill(15)
        + "000000000000000"
        + "0000"
        + "0000"
        + "000"
        + str(cc).zfill(4)
        + "000"
        + "000000000000000"
        + "P"
        + str(doc).zfill(3)
        + num_doc.zfill(11)
        + "001"
        + due_date
        + "0000"
        + "00"
    )
    if len(cxp_line) != 220:
        raise PrnValidationError(
            f"Error interno generando PRN: linea tiene {len(cxp_line)} caracteres (esperado 220)."
        )
    lines.append(cxp_line)
    sec += 1

    if plan.deductible_vat > 0:
        lines.append(
            _format_item_line(
                sec=sec,
                doc=doc,
                num_doc=num_doc,
                fecha=fecha,
                cc=cc,
                cuenta="2408020100",
                producto="0000000000000",
                descripcion="INCOLMOTOS SAS",
                deb_cred="D",
                valor=plan.deductible_vat,
                cantidad=1,
            )
        )

    return lines
