"""
siigo_client.py — Cliente para Siigo Nube API v1

Soporta sandbox y produccion. El token se refresca automaticamente
antes de expirar. Cada metodo publico lanza SiigoAPIError en caso de fallo.

Ref: https://developer.siigo.com/reference
"""

import os
import time
import requests
from datetime import datetime


SANDBOX_BASE = "https://api.sandbox.siigo.com"
PROD_BASE    = "https://api.siigo.com"


class SiigoAuthError(Exception):
    pass


class SiigoAPIError(Exception):
    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        super().__init__(f"Siigo {status_code}: {body[:300]}")


# ---------------------------------------------------------------------------
# Cliente principal
# ---------------------------------------------------------------------------

class SiigoClient:
    def __init__(
        self,
        username: str,
        access_key: str,
        partner_id: str,
        sandbox: bool = True,
    ):
        self.username   = username
        self.access_key = access_key
        self.partner_id = partner_id
        self.base_url   = SANDBOX_BASE if sandbox else PROD_BASE
        self.sandbox    = sandbox

        self._token: str | None = None
        self._token_expires_at: float = 0.0

    # -----------------------------------------------------------------------
    # Autenticacion
    # -----------------------------------------------------------------------

    def _authenticate(self):
        """
        POST /auth — obtiene access_token.
        Guarda el token y calcula su ventana de validez.
        """
        resp = requests.post(
            f"{self.base_url}/auth",
            json={"username": self.username, "access_key": self.access_key},
            headers={"Partner-Id": self.partner_id, "Content-Type": "application/json"},
            timeout=15,
        )
        if not resp.ok:
            raise SiigoAuthError(
                f"Autenticacion fallida ({resp.status_code}): {resp.text[:200]}"
            )
        data = resp.json()
        self._token = data["access_token"]
        # Renovar 60 s antes del vencimiento real
        self._token_expires_at = time.time() + data.get("expires_in", 3600) - 60

    def _token_valid(self) -> bool:
        return bool(self._token) and time.time() < self._token_expires_at

    def _headers(self) -> dict:
        if not self._token_valid():
            self._authenticate()
        return {
            "Authorization": f"Bearer {self._token}",
            "Partner-Id":    self.partner_id,
            "Content-Type":  "application/json",
        }

    # -----------------------------------------------------------------------
    # HTTP helpers
    # -----------------------------------------------------------------------

    def _get(self, path: str, params: dict | None = None) -> dict | list:
        resp = requests.get(
            f"{self.base_url}{path}",
            params=params,
            headers=self._headers(),
            timeout=15,
        )
        if not resp.ok:
            raise SiigoAPIError(resp.status_code, resp.text)
        return resp.json()

    def _post(self, path: str, payload: dict) -> dict:
        resp = requests.post(
            f"{self.base_url}{path}",
            json=payload,
            headers=self._headers(),
            timeout=30,
        )
        if not resp.ok:
            raise SiigoAPIError(resp.status_code, resp.text)
        return resp.json()

    # -----------------------------------------------------------------------
    # Verificacion de conexion
    # -----------------------------------------------------------------------

    def ping(self) -> bool:
        """Retorna True si las credenciales son validas."""
        try:
            self._authenticate()
            return True
        except (SiigoAuthError, requests.RequestException):
            return False

    # -----------------------------------------------------------------------
    # Catalogos (necesarios para parametrizar el dashboard)
    # -----------------------------------------------------------------------

    def get_document_types(self) -> list[dict]:
        """Tipos de documento configurados en la cuenta (filtrar por type='FV' o 'FC')."""
        data = self._get("/v1/document-types")
        return data if isinstance(data, list) else data.get("results", [])

    def get_taxes(self) -> list[dict]:
        """Impuestos disponibles (IVA, INC, etc.)."""
        data = self._get("/v1/taxes")
        return data if isinstance(data, list) else data.get("results", [])

    def get_payment_types(self) -> list[dict]:
        """Formas de pago configuradas."""
        data = self._get("/v1/payment-types")
        return data if isinstance(data, list) else data.get("results", [])

    def get_users(self) -> list[dict]:
        """Usuarios/vendedores de la cuenta (se necesita el ID del seller)."""
        data = self._get("/v1/users")
        return data if isinstance(data, list) else data.get("results", [])

    # -----------------------------------------------------------------------
    # Crear factura de compra
    # -----------------------------------------------------------------------

    def create_purchase_invoice(
        self,
        invoice_data: dict,
        document_id: int,
        payment_type_id: int,
        seller_id: int,
        tax_id: int = 19,
        rete_fuente_pct: float = 0.0,
        rete_ica_pct: float = 0.0,
    ) -> dict:
        """
        Crea una factura de compra en Siigo y retorna la respuesta JSON.

        Parametros:
          invoice_data    — dict extraido por ContaFlow
          document_id     — ID del tipo de documento en Siigo
                            (obtener con get_document_types())
          payment_type_id — ID de la forma de pago
                            (obtener con get_payment_types())
          seller_id       — ID del usuario responsable
                            (obtener con get_users())
          tax_id          — ID del impuesto IVA en el catalogo Siigo
                            (obtener con get_taxes() — NO es el porcentaje)
          rete_fuente_pct — Porcentaje de retencion en la fuente (ej: 3.5)
          rete_ica_pct    — Porcentaje de ReteICA (ej: 0.414)
        """
        payload = self._build_payload(
            invoice_data, document_id, payment_type_id,
            seller_id, tax_id, rete_fuente_pct, rete_ica_pct,
        )
        return self._post("/v1/invoices", payload)

    # -----------------------------------------------------------------------
    # Construccion del payload
    # -----------------------------------------------------------------------

    def _build_payload(
        self,
        data: dict,
        document_id: int,
        payment_type_id: int,
        seller_id: int,
        tax_id: int,
        rete_fuente_pct: float,
        rete_ica_pct: float,
    ) -> dict:
        """
        Mapea los campos de ContaFlow al esquema JSON de Siigo API v1.
        Ref: https://developer.siigo.com/reference/createinvoice
        """
        subtotal    = float(data.get("subtotal") or 0)
        total       = float(data.get("total_factura") or 0)
        fecha       = str(data.get("fecha_emision") or datetime.now().strftime("%Y-%m-%d"))
        vencimiento = str(data.get("fecha_vencimiento") or fecha)
        nit         = (
            str(data.get("proveedor_nit") or "")
            .replace("-", "")
            .replace(".", "")
        )

        items = [
            {
                "code":        "COMP_GEN",
                "description": (
                    f"Factura {data.get('numero_factura', 'S/N')} | "
                    f"{data.get('proveedor_nombre', 'Proveedor')}"
                ),
                "quantity": 1,
                "price":    subtotal,
                "discount": 0,
                "taxes":    [{"id": tax_id}] if tax_id else [],
            }
        ]

        retentions = []
        if rete_fuente_pct > 0:
            retentions.append({"id": 1, "percentage": rete_fuente_pct})
        if rete_ica_pct > 0:
            retentions.append({"id": 2, "percentage": rete_ica_pct})

        payload = {
            "document":   {"id": document_id},
            "date":       fecha,
            "seller":     seller_id,
            "customer":   {"identification": nit, "branch_office": 0},
            "currency":   {"code": "COP", "exchange_rate": 1},
            "items":      items,
            "payments":   [{"id": payment_type_id, "value": total, "due_date": vencimiento}],
            "observations": (
                f"ContaFlow | {data.get('numero_factura')} | NIT {data.get('proveedor_nit')}"
            ),
        }
        if retentions:
            payload["retentions"] = retentions

        return payload


# ---------------------------------------------------------------------------
# Factory desde variables de entorno
# ---------------------------------------------------------------------------

def from_env(sandbox: bool | None = None) -> SiigoClient:
    """
    Crea un SiigoClient leyendo credenciales del entorno (.env o variables del sistema).

    Variables requeridas:
      SIIGO_USERNAME    — email registrado en Siigo
      SIIGO_ACCESS_KEY  — llave generada en el panel de Siigo
      SIIGO_PARTNER_ID  — ID de partner asignado por Siigo
      SIIGO_SANDBOX     — "true" o "false" (por defecto "true")
    """
    username   = os.environ.get("SIIGO_USERNAME", "")
    access_key = os.environ.get("SIIGO_ACCESS_KEY", "")
    partner_id = os.environ.get("SIIGO_PARTNER_ID", "")

    if not all([username, access_key, partner_id]):
        missing = [
            k for k, v in {
                "SIIGO_USERNAME":   username,
                "SIIGO_ACCESS_KEY": access_key,
                "SIIGO_PARTNER_ID": partner_id,
            }.items() if not v
        ]
        raise EnvironmentError(f"Faltan variables de entorno de Siigo: {', '.join(missing)}")

    if sandbox is None:
        sandbox = os.environ.get("SIIGO_SANDBOX", "true").lower() != "false"

    return SiigoClient(username, access_key, partner_id, sandbox=sandbox)
