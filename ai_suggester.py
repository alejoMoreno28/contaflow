"""
ai_suggester.py — Sugerencia de cuenta contable + impuesto via Claude Haiku

Optimización de tokens (dos etapas antes de llamar a Haiku):
  1. Filtro de clase PUC: solo cuentas con código PUC que empiece por
     14, 15, 5 o 6 (inventarios, activos fijos, gastos, costos).
  2. Filtro de keywords: dentro de las cuentas permitidas, las 50 más
     relevantes por coincidencia de palabras clave.

La función retorna un dict {"account_id": int|None, "tax_id": int|None}.
"""

import json as _json
import os
import re

import anthropic

# Prefijos PUC admitidos para facturas de compra
_PURCHASE_PREFIXES = ("14", "15", "5", "6")


# ---------------------------------------------------------------------------
# Helpers de filtrado
# ---------------------------------------------------------------------------

def _get_puc_code(account: dict) -> str:
    """Extrae el código PUC del campo 'code'."""
    return str(account.get("code", "")).strip()


def _filter_by_class(accounts: list[dict]) -> list[dict]:
    """
    Retiene SOLO cuentas cuyo código PUC empiece por 14, 15, 5 o 6.
    El código PUC está al inicio del campo 'name': "143005 — Productos..."
    """
    filtered = []
    for a in accounts:
        code = _get_puc_code(a)
        if any(code.startswith(p) for p in _PURCHASE_PREFIXES):
            filtered.append(a)
    return filtered


def _filter_by_keywords(accounts: list[dict], description: str, max_accounts: int = 50) -> list[dict]:
    """Retiene las cuentas más relevantes por coincidencia de palabras clave."""
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


def _first_expense_account(accounts: list[dict]) -> int | None:
    """Plan B: primera cuenta clase 5 (gastos) del catálogo filtrado."""
    for a in accounts:
        code = _get_puc_code(a)
        if code.startswith("5"):
            return a["id"]
    return None


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def suggest_account_for_item(
    item_description: str,
    provider_name: str,
    alegra_accounts: list[dict],
    alegra_taxes: list[dict] | None = None,
) -> dict:
    """
    Sugiere cuenta contable e impuesto para un ítem de factura.

    Parámetros:
    - item_description: descripción del ítem
    - provider_name: nombre del proveedor
    - alegra_accounts: lista [{id, name}, ...] ya filtrada por _filter_imputable
    - alegra_taxes: lista [{id, name, percentage}, ...] del catálogo de Alegra

    Retorna: {"account_id": int|None, "tax_id": int|None}
    """
    _empty = {"account_id": None, "tax_id": None}

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or not alegra_accounts or not item_description.strip():
        return _empty

    # ── Filtrar catálogo ───────────────────────────────────────────────────
    class_filtered = _filter_by_class(alegra_accounts)
    final_filtered = _filter_by_keywords(class_filtered, item_description, max_accounts=50)

    # IDs válidos para validar la respuesta de Haiku
    valid_account_ids = {a["id"] for a in final_filtered}

    # ── Construir catálogo para el prompt ──────────────────────────────────
    catalog_list = [
        {"id": a["id"], "puc": _get_puc_code(a), "nombre": a["name"]}
        for a in final_filtered
    ]

    # Impuestos disponibles
    taxes_list = [
        {"id": t["id"], "nombre": t["name"], "pct": t.get("percentage", 0)}
        for t in (alegra_taxes or [])
        if t.get("id")
    ]

    prompt = (
        f"Eres un contador colombiano experto en PUC.\n"
        f"Proveedor: '{provider_name}'\n"
        f"Ítem comprado: '{item_description}'\n\n"
        f"Catálogo de cuentas disponibles (usa el campo 'id' numérico):\n"
        f"{catalog_list}\n\n"
        f"Impuestos disponibles (usa el campo 'id' numérico):\n"
        f"{taxes_list}\n\n"
        f"Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:\n"
        f'{{\"account_id\": ID_NUMERICO, \"tax_id\": ID_IMPUESTO_O_NULL}}\n'
        f"Si el ítem no lleva impuesto, usa null en tax_id.\n"
        f"No incluyas markdown, comillas invertidas ni explicaciones."
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=64,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()

        # Limpiar posibles bloques markdown
        raw = re.sub(r"```(?:json)?\s*", "", raw).strip("`").strip()

        # Extraer primer objeto JSON de la respuesta
        json_match = re.search(r"\{[^}]+\}", raw)
        if not json_match:
            raise ValueError("No JSON found")

        result   = _json.loads(json_match.group())
        acct_raw = result.get("account_id")
        tax_raw  = result.get("tax_id")

        account_id = int(acct_raw) if acct_raw is not None else None
        tax_id     = int(tax_raw)  if tax_raw  is not None else None

        # Validar account_id
        if account_id not in valid_account_ids:
            account_id = None

        # Validar tax_id
        valid_tax_ids = {t["id"] for t in (alegra_taxes or [])}
        if tax_id not in valid_tax_ids:
            tax_id = None

        # Plan B: primera cuenta clase 5
        if account_id is None:
            account_id = _first_expense_account(class_filtered)

        return {"account_id": account_id, "tax_id": tax_id}

    except Exception:
        fallback_id = _first_expense_account(class_filtered)
        return {"account_id": fallback_id, "tax_id": None}