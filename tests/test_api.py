import sys
import os
from fastapi.testclient import TestClient

# Add contaflow-api to path to import main properly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "contaflow-api")))

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
