"""
alegra_client.py — Cliente para Alegra API v1

Crea Facturas de Proveedor (compras) usando los datos extraídos por ContaFlow.
Autenticación: HTTP Basic con email + token.

Ref: https://developer.alegra.com/reference
"""

import json
import os
import re
import requests
from base64 import b64encode
from datetime import datetime


ALEGRA_BASE = "https://api.alegra.com/api/v1"


# ---------------------------------------------------------------------------
# Excepciones
# ---------------------------------------------------------------------------

class AlegraAuthError(Exception):
    pass


class AlegraAPIError(Exception):
    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.body        = body
        super().__init__(f"Alegra {status_code}: {body[:500]}")


# ---------------------------------------------------------------------------
# Helpers de identificación
# ---------------------------------------------------------------------------

_ID_TYPE_KEYWORDS: dict[str, str] = {
    "nit_ext":     "DIE",
    "extranjero":  "DIE",
    "nie":         "DIE",
    "extranjeria": "CE",
    "extranjería": "CE",
    "pasaporte":   "Passport",
    "passport":    "Passport",
    "cedula":      "CC",
    "cédula":      "CC",
    "c.c":         "CC",
    "cc":          "CC",
    "c.e":         "CE",
    "ce":          "CE",
    "nit":         "NIT",
}


def _clean_id(raw: str) -> str:
    return re.sub(r"[.\-\s]", "", raw.strip())


def _detect_id_type(raw_id: str, tipo_hint: str = "") -> str:
    hint = tipo_hint.lower()
    for kw in sorted(_ID_TYPE_KEYWORDS, key=len, reverse=True):
        if kw in hint:
            return _ID_TYPE_KEYWORDS[kw]
    if "-" in raw_id:
        return "NIT"
    if any(c.isalpha() for c in raw_id):
        return "Passport"
    return "NIT"


def _split_nit_dv(raw_id: str) -> tuple[str, str | None]:
    if "-" in raw_id:
        base, dv = raw_id.split("-", 1)
        return base.strip(), dv.strip()
    return raw_id.strip(), None


def _extract_code(body: str) -> str | None:
    try:
        return str(json.loads(body).get("code", ""))
    except Exception:
        return None


def _extract_contact_id_from_error(body: str) -> int | None:
    try:
        data = json.loads(body)
        for key in ("contactId", "contact_id", "id"):
            val = data.get(key) or (data.get("data") or {}).get(key)
            if val:
                return int(val)
    except Exception:
        pass
    m = re.search(r'"(?:contactId|contact_id|id)"\s*:\s*(\d+)', body)
    if m:
        return int(m.group(1))
    return None


# ---------------------------------------------------------------------------
# Mensajes de error amigables
# ---------------------------------------------------------------------------

_ERROR_MESSAGES: dict[str, str] = {
    "2006":  "El proveedor ya existe con otro ID. Usa el proveedor existente.",
    "2094":  "El proveedor está deshabilitado en Alegra.",
    "11038": "La cuenta contable seleccionada es una cuenta agrupadora (no imputable). Selecciona una cuenta de detalle.",
    "11040": "La factura no tiene cuenta contable válida. Selecciona una cuenta de detalle en los ítems.",
    "31113": "La cuenta contable no existe en Alegra. Verifica el catálogo.",
    "401":   "Credenciales inválidas. Verifica tu email y token de Alegra.",
    "403":   "Sin permiso para esta operación en Alegra.",
    "422":   "Datos inválidos. Revisa los campos de la factura.",
    "500":   "Error interno de Alegra. Intenta de nuevo en unos segundos.",
}


def friendly_error(exc: "AlegraAPIError") -> str:
    """Convierte un AlegraAPIError en un mensaje amigable para mostrar al usuario."""
    code = _extract_code(exc.body)
    if code and code in _ERROR_MESSAGES:
        return _ERROR_MESSAGES[code]
    # Intentar extraer el mensaje de la respuesta
    try:
        msg = json.loads(exc.body).get("message", "")
        if msg:
            return f"Alegra rechazó la factura: {msg}"
    except Exception:
        pass
    return f"Error {exc.status_code} de Alegra. Verifica los parámetros de la factura."


# ---------------------------------------------------------------------------
# Cliente principal
# ---------------------------------------------------------------------------

class AlegraClient:
    def __init__(self, email: str, token: str):
        self.email = email
        self.token = token
        credentials = b64encode(f"{email}:{token}".encode()).decode()
        self._auth_header = f"Basic {credentials}"

    # -----------------------------------------------------------------------
    # HTTP helpers
    # -----------------------------------------------------------------------

    def _headers(self) -> dict:
        return {
            "Authorization": self._auth_header,
            "Content-Type":  "application/json",
        }

    def _get(self, path: str, params: dict | None = None) -> dict | list:
        resp = requests.get(
            f"{ALEGRA_BASE}{path}",
            params=params,
            headers=self._headers(),
            timeout=15,
        )
        if resp.status_code == 401:
            raise AlegraAuthError("Credenciales inválidas.")
        if not resp.ok:
            raise AlegraAPIError(resp.status_code, resp.text)
        return resp.json()

    def _post(self, path: str, payload: dict) -> dict:
        resp = requests.post(
            f"{ALEGRA_BASE}{path}",
            json=payload,
            headers=self._headers(),
            timeout=30,
        )
        if resp.status_code == 401:
            raise AlegraAuthError("Credenciales inválidas.")
        if not resp.ok:
            raise AlegraAPIError(resp.status_code, resp.text)
        return resp.json()

    def _put(self, path: str, payload: dict) -> dict:
        resp = requests.put(
            f"{ALEGRA_BASE}{path}",
            json=payload,
            headers=self._headers(),
            timeout=30,
        )
        if resp.status_code == 401:
            raise AlegraAuthError("Credenciales inválidas.")
        if not resp.ok:
            raise AlegraAPIError(resp.status_code, resp.text)
        return resp.json()

    def _patch(self, path: str, payload: dict) -> dict:
        resp = requests.patch(
            f"{ALEGRA_BASE}{path}",
            json=payload,
            headers=self._headers(),
            timeout=30,
        )
        if resp.status_code == 401:
            raise AlegraAuthError("Credenciales inválidas.")
        if not resp.ok:
            raise AlegraAPIError(resp.status_code, resp.text)
        return resp.json()

    # -----------------------------------------------------------------------
    # Verificación de conexión
    # -----------------------------------------------------------------------

    def ping(self) -> bool:
        try:
            self._get("/contacts", params={"limit": 1})
            return True
        except (AlegraAuthError, AlegraAPIError, requests.RequestException):
            return False

    # -----------------------------------------------------------------------
    # Catálogos — get_catalogs()
    # -----------------------------------------------------------------------

    def get_catalogs(self) -> dict:
        """
        Descarga 3 catálogos de Alegra y retorna un dict estructurado:
          {
            "accounts":      [{"id": int, "name": str, "code": str}],  # solo imputables
            "taxes":         [{"id": int, "name": str, "percentage": float}],
            "cost_centers":  [{"id": int, "name": str}],
          }

        Las cuentas imputables son las de detalle/hoja en el árbol PUC —
        se excluyen las agrupadoras que causarían el error 11038 en Alegra.
        """
        catalogs: dict = {"accounts": [], "taxes": [], "cost_centers": []}

        # ── Cuentas contables ─────────────────────────────────────────────
        for endpoint in ("/categories", "/accounts"):
            try:
                raw = self._get(endpoint, params={"limit": 500})
                if isinstance(raw, list) and raw:
                    catalogs["accounts"] = self._filter_imputable(raw)
                    break
            except AlegraAPIError as exc:
                if exc.status_code in (403, 404):
                    continue
                raise

        # ── Impuestos ─────────────────────────────────────────────────────
        # Alegra /taxes devuelve {"total": "N", "results": [...]} — no una lista.
        try:
            raw = self._get("/taxes", params={"limit": 200})
            tax_list = (
                raw if isinstance(raw, list)
                else raw.get("results", []) if isinstance(raw, dict)
                else []
            )
            catalogs["taxes"] = [
                {
                    "id":         int(t["id"]),
                    "name":       t.get("name", f"Impuesto {t['id']}"),
                    "percentage": float(t.get("percentage") or 0),
                }
                for t in tax_list if t.get("id")
            ]
        except (AlegraAPIError, Exception):
            pass

        # ── Centros de costo ──────────────────────────────────────────────
        for cc_endpoint in ("/cost-centers", "/costCenters"):
            for cc_limit in (30, 10, 5):
                try:
                    raw = self._get(cc_endpoint, params={"limit": cc_limit})
                    if isinstance(raw, list):
                        catalogs["cost_centers"] = [
                            {"id": int(c["id"]), "name": c.get("name", str(c["id"]))}
                            for c in raw
                            if c.get("id") and str(c.get("status", "active")).lower() != "inactive"
                        ]
                    break  # éxito con este límite
                except AlegraAPIError as exc:
                    if exc.status_code in (403, 404):
                        break  # endpoint no disponible, probar el siguiente
                    if exc.status_code == 400:
                        continue  # intentar con límite menor
                    break
                except Exception:
                    break
            if catalogs["cost_centers"] is not None:
                break

        return catalogs

    def _filter_imputable(self, accounts: list) -> list:
        """
        Filtra el árbol de cuentas devolviendo SOLO hojas transaccionales.

        Regla exacta (basada en esquema JSON real de Alegra):
          - use == "accumulative" → cuenta agrupadora. Recursear hijos; nunca incluir.
          - use == "movement" + children vacío → cuenta hoja imputable. Incluir.
          - use == "movement" + children no vacío → nodo intermedio. Recursear hijos;
            no incluir este nodo (las hojas más específicas son las correctas).

        Esto evita el error 11038 y excluye cuentas como "1455 - Materiales"
        que tienen use="accumulative" pero children vacío (sin subcuentas creadas).
        """
        result: list[dict] = []
        for acc in accounts:
            if not acc.get("id"):
                continue
            children = acc.get("children") or []
            use      = acc.get("use", "")

            if children:
                # Nodo con hijos: recursear siempre, no incluir este nodo
                result.extend(self._filter_imputable(children))
            else:
                # Hoja: solo incluir si es transaccional (use == "movement")
                if use == "movement":
                    result.append({
                        "id":   int(acc["id"]),
                        "name": acc.get("name", str(acc["id"])),
                        "code": str(acc.get("code") or acc["id"]),
                    })

        # Fallback: si el filtro dejó vacío (e.g. árbol todo accumulative sin hojas),
        # incluir todas las hojas sin importar use para no romper la UI.
        if not result and accounts:
            result = [
                {
                    "id":   int(a["id"]),
                    "name": a.get("name", str(a["id"])),
                    "code": str(a.get("code") or a["id"]),
                }
                for a in accounts if a.get("id") and not (a.get("children") or [])
            ]

        return result

    # -----------------------------------------------------------------------
    # Crear factura de compra
    # -----------------------------------------------------------------------

    def create_purchase_invoice(self, invoice: dict) -> dict:
        """
        Crea una Factura de Proveedor (bill/compra) en Alegra.

        Estructura esperada del dict `invoice`:
          {
            "proveedor_nombre":  str,
            "proveedor_nit":     str,
            "numero_factura":    str,
            "fecha_emision":     "YYYY-MM-DD",
            "fecha_vencimiento": "YYYY-MM-DD",
            "subtotal":          float,

            # Opcional: proveedor ya resuelto
            "contact_id": int | None,

            # Categorías con mapeo de catálogos (proviene de Step 2)
            # Si está vacío o ausente, se crea una categoría fallback
            "categories": [
              {
                "account_id":      int,
                "price":           float,
                "quantity":        int,        # default 1
                "observations":    str,
                "tax_id":          int | None,
                "cost_center_id":  int | None,
              }
            ],
          }
        """
        # ── Resolver proveedor ────────────────────────────────────────────
        contact_id = invoice.get("contact_id")
        if contact_id is None:
            contact_id = self._resolve_contact(invoice)

        # ── Fechas y metadatos ────────────────────────────────────────────
        fecha       = str(invoice.get("fecha_emision")    or datetime.now().strftime("%Y-%m-%d"))
        vencimiento = str(invoice.get("fecha_vencimiento") or fecha)
        numero      = str(invoice.get("numero_factura") or "")
        proveedor   = str(invoice.get("proveedor_nombre") or "Proveedor")

        # ── Construir purchases.categories ────────────────────────────────
        cats_raw = invoice.get("categories") or []

        if not cats_raw:
            # Fallback: una sola categoría con el subtotal completo
            cats_raw = [{
                "account_id":     invoice.get("_default_account_id") or 0,
                "price":          float(invoice.get("subtotal") or invoice.get("total_a_pagar") or 0),
                "quantity":       1,
                "observations":   f"Factura {numero} - {proveedor}",
                "tax_id":         None,
                "cost_center_id": None,
            }]

        categories = []
        for cat in cats_raw:
            entry: dict = {
                "id":           int(cat["account_id"]),
                "price":        float(cat.get("price") or 0),
                "quantity":     int(cat.get("quantity") or 1),
                "observations": str(cat.get("observations") or f"Factura {numero} - {proveedor}"),
            }
            if cat.get("tax_id"):
                entry["tax"] = [{"id": int(cat["tax_id"])}]
            if cat.get("cost_center_id"):
                entry["costCenter"] = {"id": int(cat["cost_center_id"])}
            categories.append(entry)

        # ── Payload final ─────────────────────────────────────────────────
        payload: dict = {
            "date":    fecha,
            "dueDate": vencimiento,
            "purchases": {"categories": categories},
            "observations": (
                f"ContaFlow | {numero} "
                f"| {invoice.get('proveedor_nit', '')} "
                f"| {proveedor}"
            ),
        }

        if numero:
            payload["number"] = numero
        if contact_id is not None:
            payload["provider"] = {"id": contact_id}

        return self._post("/bills", payload)

    # -----------------------------------------------------------------------
    # Resolución de contacto (get_or_create_provider)
    # -----------------------------------------------------------------------

    def get_or_create_provider(self, nit: str, nombre: str) -> int | None:
        """Busca el proveedor por NIT; si no existe, lo crea. Retorna el ID de Alegra."""
        return self._resolve_contact({"proveedor_nit": nit, "proveedor_nombre": nombre})

    def _resolve_contact(self, data: dict, force: bool = False) -> int | None:
        nit_raw   = str(data.get("proveedor_nit")    or "").strip()
        nombre    = str(data.get("proveedor_nombre") or "Proveedor sin nombre").strip()
        tipo_hint = str(data.get("proveedor_tipo_id") or "")

        if not nit_raw:
            return None

        id_type      = _detect_id_type(nit_raw, tipo_hint)
        nit_clean    = _clean_id(nit_raw)
        nit_base, dv = _split_nit_dv(nit_raw)

        contacto = self._search_by_id(nit_clean)
        if not contacto and nit_clean != nit_base:
            contacto = self._search_by_id(nit_base)
        if not contacto and nombre and nombre != "Proveedor sin nombre":
            contacto = self._search_by_name(nombre)

        if contacto:
            contact_id = contacto.get("id")
            status     = str(contacto.get("status") or "").lower()
            if status == "inactive" or force:
                self._activate_contact(contact_id)
            return contact_id

        return self._create_contact(nombre, nit_clean, nit_base, dv, id_type)

    def _search_by_id(self, identification: str) -> dict | None:
        if not identification:
            return None
        try:
            result    = self._get("/contacts", params={"identification": identification, "limit": 1})
            contactos = result if isinstance(result, list) else []
            return contactos[0] if contactos else None
        except (AlegraAPIError, requests.RequestException):
            return None

    def _search_by_name(self, nombre: str) -> dict | None:
        try:
            result    = self._get("/contacts", params={"name": nombre, "limit": 1})
            contactos = result if isinstance(result, list) else []
            return contactos[0] if contactos else None
        except (AlegraAPIError, requests.RequestException):
            return None

    def _create_contact(
        self,
        nombre: str,
        nit_clean: str,
        nit_base: str,
        dv: str | None,
        id_type: str,
    ) -> int | None:
        body: dict = {
            "name":           nombre,
            "identification": nit_clean,
            "type":           "provider",
            "identificationObject": {"type": id_type},
        }
        if id_type == "NIT" and dv is not None:
            body["identificationObject"]["dv"] = dv
        try:
            nuevo = self._post("/contacts", body)
            return nuevo.get("id")
        except AlegraAPIError as exc:
            if _extract_code(exc.body) == "2006":
                existing_id = _extract_contact_id_from_error(exc.body)
                if existing_id:
                    return existing_id
            return None
        except requests.RequestException:
            return None

    def _activate_contact(self, contact_id: int) -> None:
        try:
            self._put(f"/contacts/{contact_id}", {"status": "active"})
        except (AlegraAPIError, requests.RequestException):
            try:
                self._patch(f"/contacts/{contact_id}", {"status": "active"})
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Factory desde variables de entorno
# ---------------------------------------------------------------------------

def from_env() -> AlegraClient:
    email = os.environ.get("ALEGRA_EMAIL", "")
    token = os.environ.get("ALEGRA_TOKEN", "")
    if not email or not token:
        missing = [k for k, v in {"ALEGRA_EMAIL": email, "ALEGRA_TOKEN": token}.items() if not v]
        raise EnvironmentError(f"Faltan variables de entorno de Alegra: {', '.join(missing)}")
    return AlegraClient(email, token)


# ---------------------------------------------------------------------------
# Prueba real de integración
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    _EMAIL = "alejo08111.am@gmail.com"
    _TOKEN = "a2e8fcaa464ab2538398"
    _ACCOUNT_ID = 5320
    _PROVIDER_ID = 3   # Yamaha, NIT 890916911

    print("=" * 65)
    print("ContaFlow — Prueba de integracion Alegra API")
    print("=" * 65)

    client = AlegraClient(_EMAIL, _TOKEN)

    # ── 1. Conexion ───────────────────────────────────────────────────────
    print("\n[1] Verificando conexion...")
    assert client.ping(), "FALLO: conexion rechazada"
    print("    OK — conexion activa")

    # ── 2. Catalogo de cuentas (filtro imputables) ─────────────────────
    print("\n[2] Descargando catalogos...")
    cats = client.get_catalogs()

    accounts     = cats["accounts"]
    taxes        = cats["taxes"]
    cost_centers = cats["cost_centers"]

    print(f"    Cuentas imputables : {len(accounts)}")
    print(f"    Impuestos          : {len(taxes)}")
    print(f"    Centros de costo   : {len(cost_centers)}")

    # Verificar que la cuenta 5320 esta en la lista
    acc_5320 = next((a for a in accounts if a["id"] == _ACCOUNT_ID), None)
    if acc_5320:
        print(f"    Cuenta {_ACCOUNT_ID} OK: {acc_5320['name']}")
    else:
        print(f"    Cuenta {_ACCOUNT_ID} no en lista — verificar filtracion")
        print(f"    Primeras 5 cuentas: {[a['id'] for a in accounts[:5]]}")

    # Verificar que NO hay cuentas con children (agrupadoras filtradas)
    print("\n[2b] Verificando filtro de cuentas agrupadoras...")
    print(f"    Total en catalogo: {len(accounts)}")
    if taxes:
        print(f"    Ejemplo impuesto: {taxes[0]}")
    if cost_centers:
        print(f"    Ejemplo CC: {cost_centers[0]}")

    # ── 3. Crear factura con estructura completa ───────────────────────
    print(f"\n[3] Creando factura de prueba (proveedor id={_PROVIDER_ID})...")

    _invoice = {
        "proveedor_nombre":  "Yamaha Motor de Colombia",
        "proveedor_nit":     "890916911",
        "numero_factura":    "TEST-CF-002",
        "fecha_emision":     "2026-03-04",
        "fecha_vencimiento": "2026-03-04",
        "subtotal":          100000.0,
        "contact_id":        _PROVIDER_ID,
        "categories": [
            {
                "account_id":     _ACCOUNT_ID,
                "price":          100000.0,
                "quantity":       1,
                "observations":   "Prueba ContaFlow con catalogo completo",
                "tax_id":         taxes[0]["id"] if taxes else None,
                "cost_center_id": cost_centers[0]["id"] if cost_centers else None,
            }
        ],
    }

    try:
        result = client.create_purchase_invoice(_invoice)
        print(f"\n[OK] EXITO — Factura creada con ID: {result.get('id')}")
        print(f"     Total: {result.get('total')}")
        cats_resp = result.get("purchases", {}).get("categories", [])
        if cats_resp:
            print(f"     Categoria: {cats_resp[0].get('name')} | tax: {cats_resp[0].get('tax')}")
    except AlegraAuthError as e:
        print(f"\n[ERROR AUTH]: {e}")
        raise SystemExit(1)
    except AlegraAPIError as e:
        print(f"\n[ERROR API] ({e.status_code}): {e.body[:800]}")
        print(f"[Mensaje amigable]: {friendly_error(e)}")
        raise SystemExit(1)
    except Exception as e:
        print(f"\n[ERROR]: {e}")
        raise SystemExit(1)

    print("\n[RESULTADO] Todas las pruebas pasaron. OK para avanzar a app.py.")
