import sys
import os
from decimal import Decimal
from fastapi.testclient import TestClient

# Add contaflow-api to path to import main properly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "contaflow-api")))

import main
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_generate_prn_strict_structure(mock_factura):
    """
    Validation equivalent to `test_fastapi_regression.py`.
    Ensures that PRN file logic generates exact 220 chars per line.
    """
    response = client.post("/api/generate-prn", json={"facturas": [mock_factura]})
    
    # Should return a downloadable file (200 OK)
    assert response.status_code == 200
    
    # Content parsing
    content = response.content.decode('latin-1').strip().split('\r\n')
    assert len(content) > 0, "Debería generar al menos 1 línea."
    
    for i, line in enumerate(content):
        assert len(line) == 220, f"Error Estructural: La línea {i+1} mide {len(line)} y no 220."

    # Validate accounts logic exactly like the old script
    # Cuenta CXP (Subtotal + IVA = total facture)
    assert "2205010000" in content[1], "Falta cuenta 2205010000 (Proveedores)"
    if mock_factura["iva_total"] > 0:
        assert len(content) >= 3, "Debería haber al menos 3 líneas (CXP, IVA, Inventario)"
        assert "2408020100" in content[2], "Falta cuenta 2408020100 (IVA Estricto)"


def _line_value(line):
    return Decimal(line[125:140]) / 100


def test_generate_prn_capitalizes_excluded_oil_790425(mock_catalogo):
    mock_catalogo.return_value = (
        {
            "90793AV50400": {
                "producto": "0030001000122",
                "cta_inv": "1435010201",
            }
        },
        {"IBAGUE": {"cc": 7, "doc": 14}},
    )
    invoice = {
        "numero_factura": "CPFE-790425",
        "fecha": "2026-06-19",
        "ciudad": "IBAGUE",
        "direccion_entrega": "CR 5 20 39 B 1 CARMEN",
        "subtotal": 516307,
        "iva_total": 98098,
        "fecha_vto": "20260719",
        "items": [
            {
                "referencia": "90793AV50400",
                "descripcion": "ACEITE FULL SINTETICO 10W40 MA2-1000 CC",
                "cantidad": 12,
                "valor_total": 516307,
            }
        ],
    }

    response = client.post("/api/generate-prn", json={"facturas": [invoice]})

    assert response.status_code == 200
    lines = response.content.decode("latin-1").strip().split("\r\n")
    assert len(lines) == 2
    assert lines[0][36:46] == "1435020101"
    assert lines[0][46:59] == "0030001000122"
    assert _line_value(lines[0]) == Decimal("614405.00")
    assert lines[1][36:46] == "2205010000"
    assert _line_value(lines[1]) == Decimal("614405.00")


def test_generate_prn_rejects_unknown_003_without_tax_treatment(mock_catalogo):
    mock_catalogo.return_value = (
        {
            "NEW-OIL": {
                "producto": "0030001000999",
                "cta_inv": "1435020101",
            }
        },
        {"IBAGUE": {"cc": 7, "doc": 14}},
    )
    invoice = {
        "numero_factura": "CPFE-999999",
        "fecha": "2026-08-14",
        "ciudad": "IBAGUE",
        "direccion_entrega": "CR 5 20 39 B 1 CARMEN",
        "subtotal": 100,
        "iva_total": 19,
        "fecha_vto": "20260914",
        "items": [
            {
                "referencia": "NEW-OIL",
                "descripcion": "ACEITE NUEVO",
                "cantidad": 1,
                "valor_total": 100,
            }
        ],
    }

    response = client.post("/api/generate-prn", json={"facturas": [invoice]})

    assert response.status_code == 400
    assert "tratamiento de IVA" in response.json()["detail"]


class _FakeWorksheet:
    def __init__(self):
        self.appended = []

    def get_all_values(self):
        return [
            ["INVENTARIO"],
            ["INDICATIVO", "REFERENCIA", "PRODUCTO", "DESCRIPCION", "CUENTA"],
        ]

    def append_rows(self, rows, value_input_option=None):
        self.appended.extend(rows)
        self.value_input_option = value_input_option


def test_add_reference_calculates_account_and_ignores_client_account(monkeypatch):
    worksheet = _FakeWorksheet()
    monkeypatch.setattr(main, "_open_inventory_worksheet", lambda: worksheet)
    main.CACHE_INVENARIOS.clear()

    response = client.post(
        "/api/add-reference",
        json=[
            {
                "referencia": "90793AV50400",
                "producto": "0030001000122",
                "descripcion": "ACEITE FULL SINTETICO 10W40 MA2-1000 CC",
                "tratamiento_iva": "IVA_MAYOR_COSTO",
                "cta_inv": "9999999999",
            }
        ],
    )

    assert response.status_code == 200
    assert worksheet.value_input_option == "RAW"
    assert worksheet.appended[0][4] == "1435020101"
    assert worksheet.appended[0][6:9] == ["003", "001", "IVA_MAYOR_COSTO"]
    assert response.json()["references"][0]["cta_inv"] == "1435020101"
    assert main.CACHE_INVENARIOS["90793AV50400"]["cta_inv"] == "1435020101"


def test_add_reference_rejects_unknown_003_without_treatment_before_write(monkeypatch):
    worksheet = _FakeWorksheet()
    monkeypatch.setattr(main, "_open_inventory_worksheet", lambda: worksheet)

    response = client.post(
        "/api/add-reference",
        json=[
            {
                "referencia": "ACEITE-NUEVO",
                "producto": "0030001000999",
                "descripcion": "ACEITE NUEVO",
            }
        ],
    )

    assert response.status_code == 400
    assert "tratamiento de IVA" in response.json()["detail"]
    assert worksheet.appended == []
