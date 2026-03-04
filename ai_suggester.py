"""
ai_suggester.py — Sugerencia de cuenta contable via Claude Haiku

Dada la descripción de un ítem de factura y el catálogo de cuentas Alegra,
devuelve el ID de la cuenta contable más apropiada.

Optimización de tokens (dos etapas):
  1. Filtro de clase PUC: solo pasa cuentas de gastos/costos/inventarios/activos
     (clases 14, 15, 5, 6 del PUC colombiano). Esto elimina cuentas de pasivo,
     patrimonio e ingresos que nunca aplican a facturas de compra.
  2. Filtro de keywords: dentro de las cuentas permitidas, toma las 50 más
     relevantes por coincidencia de palabras clave con la descripción del ítem.
"""

import os
import re

import anthropic

# Prefijos PUC permitidos para facturas de compra:
# 14 = Inventarios, 15 = Propiedad planta y equipo,
# 5  = Gastos, 6 = Costo de ventas / Costo de producción
_PURCHASE_PREFIXES = ("14", "15", "5", "6")


def _is_purchase_account(code: str) -> bool:
    """Retorna True si el código PUC corresponde a una cuenta de compra/gasto."""
    c = str(code).strip()
    return any(c.startswith(p) for p in _PURCHASE_PREFIXES)


def _filter_by_class(accounts: list[dict]) -> list[dict]:
    """Filtra el catálogo a solo cuentas de clase 14, 15, 5 o 6 (compras/gastos)."""
    filtered = [a for a in accounts if _is_purchase_account(a.get("code", ""))]
    # Si no quedó nada (catálogo sin esas clases), devolver todo para no quedar vacío
    return filtered if filtered else accounts


def _filter_by_keywords(accounts: list[dict], description: str, max_accounts: int = 50) -> list[dict]:
    """Filtra el catálogo a las cuentas más relevantes para la descripción dada."""
    keywords = re.findall(r"[a-záéíóúñ\w]{3,}", description.lower())
    if not keywords:
        return accounts[:max_accounts]

    scored: list[tuple[int, dict]] = []
    for acc in accounts:
        name_lower = acc.get("name", "").lower()
        score = sum(1 for kw in keywords if kw in name_lower)
        if score > 0:
            scored.append((score, acc))

    scored.sort(key=lambda x: x[0], reverse=True)
    filtered = [acc for _, acc in scored[:max_accounts]]
    return filtered if filtered else accounts[:max_accounts]


def suggest_account_for_item(
    item_description: str,
    provider_name: str,
    alegra_accounts: list[dict],
) -> int | None:
    """
    Sugiere el ID de cuenta contable Alegra para un ítem de factura.

    Parámetros:
    - item_description: descripción del ítem (ej: "Aceite mineral 10W-40")
    - provider_name: nombre del proveedor (ej: "Yamaha Motor de Colombia")
    - alegra_accounts: lista [{id, name, code}, ...] del catálogo Alegra

    Retorna el ID (int) de la cuenta sugerida, o None si falla.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or not alegra_accounts or not item_description.strip():
        return None

    # Etapa 1: filtrar por clase PUC (14, 15, 5, 6) — elimina pasivos e ingresos
    class_filtered = _filter_by_class(alegra_accounts)

    # Etapa 2: filtrar por keywords, máximo 50 cuentas al prompt
    final_filtered = _filter_by_keywords(class_filtered, item_description, max_accounts=50)

    catalog_dict = {
        str(a["id"]): f"{a.get('code', '')} — {a['name']}"
        for a in final_filtered
    }

    prompt = (
        f"Eres un contador colombiano. El proveedor es '{provider_name}' y el ítem comprado es "
        f"'{item_description}'. Aquí tienes el catálogo de cuentas filtrado de este cliente en "
        f"formato JSON: {catalog_dict}. "
        f"Devuelve ÚNICAMENTE el ID (número) de la cuenta que mejor corresponda a este gasto. "
        f"No expliques nada, solo el ID."
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=16,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        match = re.search(r"\d+", raw)
        if match:
            suggested_id = int(match.group())
            valid_ids = {a["id"] for a in final_filtered}
            if suggested_id in valid_ids:
                return suggested_id
    except Exception:
        pass

    return None
