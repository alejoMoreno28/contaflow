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
        self.body        = body   # raw para inspeccionar códigos internos
        super().__init__(f"Alegra {status_code}: {body[:500]}")


# ---------------------------------------------------------------------------
# Helpers de identificación
# ---------------------------------------------------------------------------

# Tipos válidos en Alegra Colombia
_ID_TYPE_KEYWORDS: dict[str, str] = {
    "nit_ext":    "DIE",
    "extranjero": "DIE",
    "nie":        "DIE",
    "extranjeria": "CE",
    "extranjería": "CE",
    "pasaporte":  "Passport",
    "passport":   "Passport",
    "cedula":     "CC",
    "cédula":     "CC",
    "c.c":        "CC",
    "cc":         "CC",
    "c.e":        "CE",
    "ce":         "CE",
    "nit":        "NIT",
}


def _clean_id(raw: str) -> str:
    """Elimina puntos, guiones, espacios y caracteres no alfanuméricos del ID."""
    return re.sub(r"[.\-\s]", "", raw.strip())


def _detect_id_type(raw_id: str, tipo_hint: str = "") -> str:
    """
    Detecta el tipo de documento para Alegra.

    Prioridad:
      1. tipo_hint contiene palabra clave conocida  → usarla (claves más largas primero)
      2. raw_id contiene guión                      → NIT colombiano
      3. raw_id contiene letras                     → Passport
      4. Defecto                                    → NIT
    """
    hint = tipo_hint.lower()
    # Ordenar por longitud descendente para que "nit_ext" > "nit", "c.c" > "cc", etc.
    for kw in sorted(_ID_TYPE_KEYWORDS, key=len, reverse=True):
        if kw in hint:
            return _ID_TYPE_KEYWORDS[kw]

    if "-" in raw_id:
        return "NIT"
    if any(c.isalpha() for c in raw_id):
        return "Passport"
    return "NIT"


def _split_nit_dv(raw_id: str) -> tuple[str, str | None]:
    """
    Separa el NIT del dígito verificador.
    '900123456-1' → ('900123456', '1')
    '900123456'   → ('900123456', None)
    """
    if "-" in raw_id:
        base, dv = raw_id.split("-", 1)
        return base.strip(), dv.strip()
    return raw_id.strip(), None


def _extract_code(body: str) -> str | None:
    """Extrae el código de error interno de Alegra del body JSON."""
    try:
        return str(json.loads(body).get("code", ""))
    except Exception:
        return None


def _extract_contact_id_from_error(body: str) -> int | None:
    """
    Intenta extraer el contactId del body de un error de Alegra.
    Útil para el error 2006 (identificación duplicada) que incluye el ID existente.
    """
    try:
        data = json.loads(body)
        for key in ("contactId", "contact_id", "id"):
            val = data.get(key) or (data.get("data") or {}).get(key)
            if val:
                return int(val)
    except Exception:
        pass
    # Búsqueda por regex como fallback
    m = re.search(r'"(?:contactId|contact_id|id)"\s*:\s*(\d+)', body)
    if m:
        return int(m.group(1))
    return None


# ---------------------------------------------------------------------------
# Cliente principal
# ---------------------------------------------------------------------------

class AlegraClient:
    def __init__(self, email: str, token: str):
        self.email = email
        self.token = token
        credentials = b64encode(f"{email}:{token}".encode()).decode()
        self._auth_header = f"Basic {credentials}"
        raw_account_id = os.environ.get("ALEGRA_ACCOUNT_ID", "62")
        self.default_account_id: int = int(raw_account_id)
        print(f"[Alegra] Cuenta contable por defecto: ID={self.default_account_id}")

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
        print(f"\n{'='*60}")
        print(f"[Alegra] POST {ALEGRA_BASE}{path}")
        print(f"[Alegra] PAYLOAD:\n{json.dumps(payload, ensure_ascii=False, indent=2)}")
        print(f"{'='*60}")

        resp = requests.post(
            f"{ALEGRA_BASE}{path}",
            json=payload,
            headers=self._headers(),
            timeout=30,
        )

        print(f"[Alegra] STATUS: {resp.status_code}")
        print(f"[Alegra] HEADERS: {dict(resp.headers)}")
        print(f"[Alegra] BODY:\n{resp.text[:3000]}")
        print(f"{'='*60}\n")

        if resp.status_code == 401:
            raise AlegraAuthError("Credenciales inválidas.")
        if not resp.ok:
            raise AlegraAPIError(resp.status_code, resp.text)
        return resp.json()

    def _put(self, path: str, payload: dict) -> dict:
        """PUT completo — usado para activar contactos."""
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
    # Catálogos
    # -----------------------------------------------------------------------

    def get_contacts(self, query: str | None = None) -> list[dict]:
        params = {"limit": 30}
        if query:
            params["name"] = query
        data = self._get("/contacts", params=params)
        return data if isinstance(data, list) else []

    def get_warehouses(self) -> list[dict]:
        data = self._get("/warehouses")
        return data if isinstance(data, list) else []

    def get_payment_methods(self) -> list[dict]:
        data = self._get("/payment-methods")
        return data if isinstance(data, list) else []

    # -----------------------------------------------------------------------
    # Crear factura de compra — flujo principal
    # -----------------------------------------------------------------------

    def create_purchase_invoice(
        self,
        invoice_data: dict,
        contact_id: int | None = None,
        warehouse_id: int | None = None,
        payment_method_id: int | None = None,
        cost_center_id: int | None = None,
        tax_included: bool = False,
    ) -> dict:
        """
        Crea una Factura de Proveedor (bill/compra) en Alegra.

        Manejo automático de errores con máximo 3 reintentos:
          • 2094 (proveedor deshabilitado) → activa vía PUT y reintenta
          • 11040 (ítem sin cuenta)        → asegura default_account_id y reintenta
          • 31113 (cuenta no existe)       → re-fetch /accounts y reintenta
          • 2006 (ID duplicada en contacto) → usa ID existente (sin reintento extra)
        """
        MAX_RETRIES = 3

        # Paso 1 — resolver contacto si no se pasó externamente
        if contact_id is None:
            contact_id = self._resolve_contact(invoice_data)

        # Paso 2 — construir payload inicial
        payload = self._build_payload(
            invoice_data, contact_id, warehouse_id,
            payment_method_id, cost_center_id, tax_included,
        )

        # Paso 3 — intentar crear con reintentos ante errores conocidos
        last_exc: AlegraAPIError | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return self._post("/bills", payload)

            except AlegraAPIError as exc:
                last_exc = exc
                code = _extract_code(exc.body)
                print(f"[Alegra] Intento {attempt}/{MAX_RETRIES} — código de error: {code}")

                # ── 2094: proveedor deshabilitado → activar y reintentar ──────
                if code == "2094":
                    print("[Alegra] Error 2094: proveedor deshabilitado. Activando contacto...")
                    cid = (
                        contact_id
                        or _extract_contact_id_from_error(exc.body)
                        or self._resolve_contact(invoice_data, force=True)
                    )
                    if cid:
                        self._activate_contact(cid)
                        payload["provider"] = {"id": cid}
                        contact_id = cid
                    continue

                # ── 11040: ítem sin cuenta contable → inyectar cuenta ────────
                if code == "11040":
                    print("[Alegra] Error 11040: ítems sin cuenta contable. Verificando cuenta...")
                    if not self.default_account_id:
                        self._fetch_default_account()
                    if self.default_account_id:
                        for item in payload.get("items", []):
                            if "account" not in item:
                                item["account"] = {"id": self.default_account_id, "code": "6205"}
                    continue

                # ── 31113: cuenta no existe → propagar con mensaje claro ─────
                if code == "31113":
                    raise AlegraAPIError(
                        exc.status_code,
                        f"La cuenta contable ID={self.default_account_id} no existe en Alegra. "
                        f"Actualiza ALEGRA_ACCOUNT_ID en .env. Detalle: {exc.body}",
                    )

                # ── Otros errores → propagar inmediatamente ──────────────────
                raise

        raise last_exc or AlegraAPIError(0, "Máximo de reintentos alcanzado.")

    # -----------------------------------------------------------------------
    # Resolución de contacto: 6 pasos
    # -----------------------------------------------------------------------

    def _resolve_contact(self, data: dict, force: bool = False) -> int | None:
        """
        Garantiza que el proveedor existe y está activo en Alegra.

        Pasos:
          1. Limpiar identificación (quitar puntos, guiones, espacios)
          2. Buscar por identificación limpia
          3. Buscar por identificación base (sin dígito verificador)
          4. Buscar por nombre
          5. Activar si se encontró inactivo
          6. Crear si no existe → manejar error 2006 en creación

        Soporta: NIT, CC, CE, Passport, DIE (NIT extranjero)
        """
        nit_raw   = str(data.get("proveedor_nit")    or "").strip()
        nombre    = str(data.get("proveedor_nombre") or "Proveedor sin nombre").strip()
        tipo_hint = str(data.get("proveedor_tipo_id") or "")

        if not nit_raw:
            print(f"[Alegra] Sin identificación para '{nombre}'; factura sin contacto.")
            return None

        id_type      = _detect_id_type(nit_raw, tipo_hint)
        nit_clean    = _clean_id(nit_raw)           # sin puntos/guiones/espacios
        nit_base, dv = _split_nit_dv(nit_raw)       # base + DV si aplica

        print(f"[Alegra] Resolviendo contacto | tipo={id_type} | raw='{nit_raw}' | limpio='{nit_clean}'")

        contacto = None

        # Paso 2 — Buscar por ID limpio
        contacto = self._search_by_id(nit_clean)

        # Paso 3 — Buscar por ID base (ej: '900123456' de '900123456-1')
        if not contacto and nit_clean != nit_base:
            contacto = self._search_by_id(nit_base)

        # Paso 4 — Buscar por nombre
        if not contacto and nombre and nombre != "Proveedor sin nombre":
            contacto = self._search_by_name(nombre)

        # Paso 5 — Contacto encontrado: activar si es necesario
        if contacto:
            contact_id = contacto.get("id")
            status     = str(contacto.get("status") or "").lower()
            if status == "inactive" or force:
                self._activate_contact(contact_id)
            print(f"[Alegra] Contacto listo | ID={contact_id} | estado='{status}'")
            return contact_id

        # Paso 6 — No existe: crear (maneja error 2006 internamente)
        return self._create_contact(nombre, nit_clean, nit_base, dv, id_type)

    def _search_by_id(self, identification: str) -> dict | None:
        """Busca un contacto por número de identificación. Retorna el primero o None."""
        if not identification:
            return None
        try:
            result    = self._get("/contacts", params={"identification": identification, "limit": 1})
            contactos = result if isinstance(result, list) else []
            if contactos:
                print(f"[Alegra] Encontrado por ID '{identification}': ID={contactos[0].get('id')}")
                return contactos[0]
        except (AlegraAPIError, requests.RequestException) as exc:
            print(f"[Alegra] Error buscando por ID '{identification}': {exc}")
        return None

    def _search_by_name(self, nombre: str) -> dict | None:
        """Busca un contacto por nombre. Retorna el primero o None."""
        try:
            result    = self._get("/contacts", params={"name": nombre, "limit": 1})
            contactos = result if isinstance(result, list) else []
            if contactos:
                print(f"[Alegra] Encontrado por nombre '{nombre}': ID={contactos[0].get('id')}")
                return contactos[0]
        except (AlegraAPIError, requests.RequestException) as exc:
            print(f"[Alegra] Error buscando por nombre '{nombre}': {exc}")
        return None

    def _create_contact(
        self,
        nombre: str,
        nit_clean: str,
        nit_base: str,
        dv: str | None,
        id_type: str,
    ) -> int | None:
        """Crea un nuevo contacto proveedor en Alegra (paso 6)."""
        print(f"[Alegra] Creando contacto '{nombre}' ({id_type} {nit_clean})...")
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
            cid   = nuevo.get("id")
            print(f"[Alegra] Contacto creado con ID {cid} (tipo {id_type}).")
            return cid
        except AlegraAPIError as exc:
            code = _extract_code(exc.body)
            # 2006: ya existe con esa identificación → extraer ID y usarlo
            if code == "2006":
                print("[Alegra] Error 2006 al crear: identificación ya existe. Extrayendo ID...")
                existing_id = _extract_contact_id_from_error(exc.body)
                if existing_id:
                    print(f"[Alegra] Usando contacto existente ID={existing_id}.")
                    return existing_id
            print(f"[Alegra] Error creando contacto: {exc}")
            return None
        except requests.RequestException as exc:
            print(f"[Alegra] Error de red creando contacto: {exc}")
            return None

    def _activate_contact(self, contact_id: int) -> None:
        """Activa un contacto inactivo vía PUT /contacts/{id}."""
        print(f"[Alegra] Activando contacto ID {contact_id} vía PUT...")
        try:
            self._put(f"/contacts/{contact_id}", {"status": "active"})
            print(f"[Alegra] Contacto ID {contact_id} activado correctamente.")
        except (AlegraAPIError, requests.RequestException) as exc:
            print(f"[Alegra] No se pudo activar contacto ID {contact_id}: {exc}")
            # Intentar con PATCH como fallback
            try:
                self._patch(f"/contacts/{contact_id}", {"status": "active"})
                print(f"[Alegra] Contacto ID {contact_id} activado vía PATCH (fallback).")
            except Exception as exc2:
                print(f"[Alegra] PATCH también falló: {exc2}")

    # -----------------------------------------------------------------------
    # Construcción del payload de factura
    # -----------------------------------------------------------------------

    def _build_payload(
        self,
        data: dict,
        contact_id: int | None,
        warehouse_id: int | None,
        payment_method_id: int | None,
        cost_center_id: int | None,
        tax_included: bool,
    ) -> dict:
        """
        Mapea los campos de ContaFlow al esquema JSON de Alegra Bills API.
        Incluye 'account' en cada ítem si hay default_account_id.
        Ref: https://developer.alegra.com/reference/createbill
        """
        fecha          = str(data.get("fecha_emision")    or datetime.now().strftime("%Y-%m-%d"))
        vencimiento    = str(data.get("fecha_vencimiento") or fecha)
        porcentaje_iva = float(data.get("porcentaje_iva") or 0)

        # ── Ítems ─────────────────────────────────────────────────────────────
        items_raw = data.get("items") or []
        if isinstance(items_raw, str):
            try:
                items_raw = json.loads(items_raw)
            except Exception:
                items_raw = []

        # Construir ítems; si la lista queda vacía tras el filtro, usar fallback
        items = [
            self._build_alegra_item(item, porcentaje_iva, tax_included)
            for item in items_raw
            if item.get("descripcion")
        ]

        if not items:
            subtotal = float(data.get("subtotal") or 0)
            fallback: dict = {
                "description": (
                    f"Factura {data.get('numero_factura', 'S/N')} – "
                    f"{data.get('proveedor_nombre', 'Proveedor')}"
                ),
                "quantity": 1,
                "price":    subtotal,
            }
            if porcentaje_iva > 0:
                fallback["tax"] = [{"percentage": porcentaje_iva}]
            if self.default_account_id:
                fallback["account"] = {"id": self.default_account_id}
            items = [fallback]

        # ── Payload base ──────────────────────────────────────────────────────
        payload: dict = {
            "date":    fecha,
            "dueDate": vencimiento,
            "items":   items,
            "observations": (
                f"ContaFlow | {data.get('numero_factura')} "
                f"| {data.get('proveedor_nit')} "
                f"| {data.get('proveedor_nombre')}"
            ),
        }

        # Cuenta contable a nivel de factura (además de en cada ítem)
        if self.default_account_id:
            payload["account"] = {"id": self.default_account_id}

        # provider SIEMPRE incluido si tenemos contact_id
        if contact_id is not None:
            payload["provider"] = {"id": contact_id}

        if warehouse_id:
            payload["warehouse"]     = {"id": warehouse_id}
        if payment_method_id:
            payload["paymentMethod"] = {"id": payment_method_id}
        if cost_center_id:
            payload["costCenter"]    = {"id": cost_center_id}

        return payload

    def _build_alegra_item(self, item: dict, porcentaje_iva: float, tax_included: bool) -> dict:
        """Convierte un ítem de ContaFlow al formato esperado por Alegra."""
        descripcion = str(item.get("descripcion") or "Producto/Servicio").strip()
        cantidad    = float(item.get("cantidad") or 1)
        precio      = float(item.get("valor_unitario") or item.get("valor_total") or 0)

        if not item.get("valor_unitario") and item.get("valor_total") and cantidad:
            precio = float(item["valor_total"]) / cantidad

        alegra_item: dict = {
            "description": descripcion,
            "quantity":    cantidad,
            "price":       round(precio, 2),
        }

        # IVA solo si aplica
        if porcentaje_iva > 0:
            alegra_item["tax"] = [{"percentage": porcentaje_iva}]

        # Cuenta contable en cada ítem
        if self.default_account_id:
            alegra_item["account"] = {"id": self.default_account_id}

        return alegra_item


# ---------------------------------------------------------------------------
# Factory desde variables de entorno
# ---------------------------------------------------------------------------

def from_env() -> AlegraClient:
    """
    Crea un AlegraClient leyendo credenciales del entorno (.env o variables del sistema).

    Variables requeridas:
      ALEGRA_EMAIL — email de la cuenta Alegra
      ALEGRA_TOKEN — token de API generado en Configuración → API en Alegra
    """
    email = os.environ.get("ALEGRA_EMAIL", "")
    token = os.environ.get("ALEGRA_TOKEN", "")

    if not email or not token:
        missing = [k for k, v in {"ALEGRA_EMAIL": email, "ALEGRA_TOKEN": token}.items() if not v]
        raise EnvironmentError(f"Faltan variables de entorno de Alegra: {', '.join(missing)}")

    return AlegraClient(email, token)
