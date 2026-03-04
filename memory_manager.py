"""
memory_manager.py — Memoria persistente por proveedor (NIT → mapeos Alegra)

Guarda y lee supplier_memory.json usando ruta absoluta relativa al módulo,
garantizando compatibilidad con Railway y cualquier entorno.

Esquema del JSON:
{
  "<NIT>": {
    "cuenta_id":       int | null,   # cuenta por defecto para este proveedor
    "impuesto_id":     int | null,
    "centro_costo_id": int | null,
    "items": {
      "<item_key>": {               # clave normalizada de la descripción
        "cuenta_id":       int | null,
        "impuesto_id":     int | null,
        "centro_costo_id": int | null,
      }
    }
  }
}
"""

import json
import os
import re

_MEMORY_PATH = os.path.join(os.path.dirname(__file__), "supplier_memory.json")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_item_key(description: str) -> str:
    """Normaliza una descripción de ítem para usarla como clave de memoria."""
    key = re.sub(r"[^a-z0-9]", "_", description.lower().strip())
    key = re.sub(r"_+", "_", key).strip("_")
    return key[:60]


def _load() -> dict:
    if os.path.exists(_MEMORY_PATH):
        try:
            with open(_MEMORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save(memory: dict) -> None:
    with open(_MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def get_nit_memory(nit: str) -> dict:
    """
    Retorna la memoria completa de un NIT:
    {"cuenta_id": int|None, "impuesto_id": int|None, "centro_costo_id": int|None,
     "items": {...}}
    """
    nit = str(nit).strip()
    if not nit:
        return {}
    return _load().get(nit, {})


def save_nit_memory(
    nit: str,
    cuenta_id: int | None = None,
    impuesto_id: int | None = None,
    centro_costo_id: int | None = None,
) -> None:
    """Guarda el mapeo de cuenta/impuesto/cc a nivel de NIT (valor por defecto del proveedor)."""
    nit = str(nit).strip()
    if not nit:
        return
    memory = _load()
    entry  = memory.setdefault(nit, {})
    if cuenta_id is not None:
        entry["cuenta_id"]       = int(cuenta_id)
    if impuesto_id is not None:
        entry["impuesto_id"]     = int(impuesto_id)
    if centro_costo_id is not None:
        entry["centro_costo_id"] = int(centro_costo_id)
    _save(memory)


def save_item_memory(
    nit: str,
    item_description: str,
    cuenta_id: int | None = None,
    impuesto_id: int | None = None,
    centro_costo_id: int | None = None,
) -> None:
    """Guarda el mapeo de cuenta/impuesto/cc para un ítem específico de un proveedor."""
    nit = str(nit).strip()
    if not nit or not item_description:
        return
    key    = normalize_item_key(item_description)
    memory = _load()
    entry  = memory.setdefault(nit, {})
    items  = entry.setdefault("items", {})
    items[key] = {
        "cuenta_id":       int(cuenta_id)       if cuenta_id       is not None else None,
        "impuesto_id":     int(impuesto_id)     if impuesto_id     is not None else None,
        "centro_costo_id": int(centro_costo_id) if centro_costo_id is not None else None,
    }
    _save(memory)


def get_item_memory(nit: str, item_description: str) -> dict:
    """
    Retorna el mapeo para un ítem específico de un proveedor.
    Si no hay memoria de ítem, usa la memoria de nivel NIT como fallback.
    Retorna dict con keys: cuenta_id, impuesto_id, centro_costo_id (pueden ser None).
    """
    nit = str(nit).strip()
    key = normalize_item_key(item_description)
    nit_mem = get_nit_memory(nit)

    # Intentar memoria específica del ítem primero
    item_mem = nit_mem.get("items", {}).get(key, {})
    if item_mem:
        return item_mem

    # Fallback: memoria a nivel de NIT
    return {
        "cuenta_id":       nit_mem.get("cuenta_id"),
        "impuesto_id":     nit_mem.get("impuesto_id"),
        "centro_costo_id": nit_mem.get("centro_costo_id"),
    }


def save_invoice_memory(nit: str, items: list[dict]) -> None:
    """
    Guarda la memoria de todos los ítems de una factura en una sola operación.
    Cada item dict debe tener: descripcion, cuenta_id, impuesto_id, centro_costo_id.
    """
    nit = str(nit).strip()
    if not nit or not items:
        return
    memory = _load()
    entry  = memory.setdefault(nit, {})
    items_mem = entry.setdefault("items", {})

    for item in items:
        desc = str(item.get("descripcion") or "")
        if not desc:
            continue
        key = normalize_item_key(desc)
        items_mem[key] = {
            "cuenta_id":       int(item["cuenta_id"])       if item.get("cuenta_id")       is not None else None,
            "impuesto_id":     int(item["impuesto_id"])     if item.get("impuesto_id")     is not None else None,
            "centro_costo_id": int(item["centro_costo_id"]) if item.get("centro_costo_id") is not None else None,
        }

    # Guardar también el mapeo a nivel NIT (usando el primer item con cuenta definida)
    first = next((i for i in items if i.get("cuenta_id") is not None), None)
    if first:
        entry.setdefault("cuenta_id",       first.get("cuenta_id"))
        entry.setdefault("impuesto_id",     first.get("impuesto_id"))
        entry.setdefault("centro_costo_id", first.get("centro_costo_id"))

    _save(memory)


def forget_nit(nit: str) -> None:
    """Elimina toda la memoria de un NIT."""
    nit = str(nit).strip()
    memory = _load()
    if nit in memory:
        del memory[nit]
        _save(memory)
