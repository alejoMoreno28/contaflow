"""Reglas contables y tributarias compartidas para repuestos Yamaha."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


IVA_MAYOR_COSTO = "IVA_MAYOR_COSTO"
DESCONTABLE = "DESCONTABLE"
CTA_ACEITES = "1435020101"


class YamahaRuleError(ValueError):
    """Señala un dato que no puede clasificarse contablemente con seguridad."""


@dataclass(frozen=True)
class ApprovedOil:
    producto: str
    descripcion: str


def _oil(elemento: str, descripcion: str) -> ApprovedOil:
    return ApprovedOil(producto=f"0030001{elemento}", descripcion=descripcion)


EXCLUDED_OILS: dict[str, ApprovedOil] = {
    "90793AA20800": _oil("000001", "ACEITE YAMALUBE 2T"),
    "90793AV40100": _oil("000003", "ACEITE 4T 20W-50"),
    "80W90": _oil("000004", "ACEITE TRASMISION YW100"),
    "ACCY2R0000": _oil("000008", "ACEITTE YAMALUBE 2R RACIN 32 ON"),
    "SAE10": _oil("000010", "ACEITE TELESCOPICO SAE-10 PINTA"),
    "5MR500": _oil("000101", "ACEITE TELESCOPICO X 500CC"),
    "90793AV20100": _oil("000102", "ACEITE 2 TIEMPOS"),
    "90793AY40300": _oil("000103", "ACEITE RACING 10W/50 SEMISINTE"),
    "90793AY40700": _oil("000104", "ACEITE ATV 05W40 SEMI SINTETIC"),
    "90793AY80100": _oil("000105", "ACEITE AT GEAR 10W30 140CC"),
    "ACHIDRAULICO": _oil("000106", "ACEITE HIDRAULICO"),
    "90793AV20200": _oil("000107", "ACEITE YAMALUBE 2T"),
    "90793AV40200": _oil("000108", "ACEITE YAMALUBE 4T"),
    "90793AY40200": _oil("000111", "15W50 FULL SINTE + ESTER 946ML"),
    "90793AY41500": _oil("000112", "ACEITE MOTOR AUTOMATICAS YW-NEXT"),
    "V90793AV40200": _oil("000113", "ACEITE YAMALUBE 4T"),
    "ACEITEVALVULINASYFM450": _oil("000114", "ACEITE VALVULINAS YFM450"),
    "90793AV41500": _oil("000115", "20W40 ACEITE MOTOR AUTOM 900ML"),
    "90793AV50100": _oil("000116", "10W40 SEMISINTETICO"),
    "90793AV20300": _oil("000117", "ACEITE YAMALUBE 2T LITRO"),
    "90793AV50200": _oil("000118", "ACEITE 10W40 MA2"),
    "90793AV50300": _oil("000119", "ACEITE 10W40 MB 900 CC"),
    "90793AV41600": _oil("000120", "ACEITE 20W50 YAMALUBE 4T 1LT"),
    "3374650255668": _oil("000121", "ACEITE MOTUL SCOOTER 10W40 1L"),
    "90793AV50400": _oil("000122", "ACEITE FULL SINTETICO 10W40 MA2-1000 CC"),
    "90793AV81700": _oil("000125", "ACEITE AT GEAR 10W30 140CC"),
    "90793AV41800": _oil("000127", "ACEITE 20W50 YAMALUBE 4T LITRO"),
    "90793AV81800": _oil("000128", "ACEITE DE SUSPENSION 1LT"),
}


def normalize_reference(value: object) -> str:
    return str(value).strip() if value is not None else ""


def normalize_product_code(value: object) -> str:
    code = str(value).strip() if value is not None else ""
    if code.startswith("'"):
        code = code[1:].strip()
    if len(code) != 13 or not code.isdigit():
        raise YamahaRuleError("El codigo producto debe tener exactamente 13 digitos.")
    return code


def product_line_group(value: object) -> tuple[str, str]:
    code = normalize_product_code(value)
    return code[:3], code[3:7]


def is_oil_product(value: object) -> bool:
    return product_line_group(value) == ("003", "0001")


def calcular_cta_inv(codigo_producto: object) -> str:
    code = normalize_product_code(codigo_producto)
    line, group = product_line_group(code)

    if line == "002":
        group_number = int(group)
        if group_number > 99:
            raise YamahaRuleError(
                f"El producto {code} usa un grupo 002 sin regla contable confirmada."
            )
        return f"14350102{group_number:02d}"

    if (line, group) == ("003", "0001"):
        return CTA_ACEITES

    raise YamahaRuleError(
        f"El producto {code} pertenece a una familia sin regla contable confirmada."
    )


def normalize_tax_treatment(value: object) -> str | None:
    text = str(value).strip().upper() if value is not None else ""
    aliases = {
        "": None,
        IVA_MAYOR_COSTO: IVA_MAYOR_COSTO,
        "MAYOR_COSTO": IVA_MAYOR_COSTO,
        "EXCLUIDA": IVA_MAYOR_COSTO,
        "SI": IVA_MAYOR_COSTO,
        DESCONTABLE: DESCONTABLE,
        "GRAVADA": DESCONTABLE,
        "NO": DESCONTABLE,
    }
    if text not in aliases:
        raise YamahaRuleError(f"Tratamiento de IVA no reconocido: {value!r}.")
    return aliases[text]


def resolve_tax_treatment(
    explicit_value: object,
    referencia: object,
    producto: object,
) -> str | None:
    explicit = normalize_tax_treatment(explicit_value)
    if explicit:
        return explicit

    ref = normalize_reference(referencia)
    if ref in EXCLUDED_OILS:
        return IVA_MAYOR_COSTO

    line, group = product_line_group(producto)
    if line == "002":
        return DESCONTABLE
    if (line, group) == ("003", "0001"):
        return None
    return None


def enrich_catalog_with_known_oils(
    catalog: Mapping[str, Mapping[str, object]],
) -> dict[str, dict[str, object]]:
    enriched = {normalize_reference(ref): dict(data) for ref, data in catalog.items()}

    for referencia, oil in EXCLUDED_OILS.items():
        current = enriched.get(referencia)
        if current is None:
            enriched[referencia] = {
                "producto": oil.producto,
                "descripcion": oil.descripcion,
                "cta_inv": CTA_ACEITES,
                "linea": "003",
                "grupo": "0001",
                "tratamiento_iva": IVA_MAYOR_COSTO,
            }
            continue

        current_product = normalize_product_code(current.get("producto", ""))
        if current_product != oil.producto:
            raise YamahaRuleError(
                "Se encontro un conflicto para la referencia "
                f"{referencia}: catalogo={current_product}, aprobado={oil.producto}."
            )
        current["cta_inv"] = CTA_ACEITES
        current["linea"] = "003"
        current["grupo"] = "0001"
        current["tratamiento_iva"] = IVA_MAYOR_COSTO

    return enriched
