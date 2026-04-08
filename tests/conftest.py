import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_catalogo():
    with patch("main.get_catalogo") as mock_cat:
        # inv, tiendas
        mock_cat.return_value = (
            {"90793AQ82100": {"producto": "YAMALUBE", "cta_inv": "1435010210"}},
            {"GIRARDOT": {"cc": 95, "doc": 240}}
        )
        yield mock_cat

@pytest.fixture
def mock_factura():
    return {
        "numero_factura": "CPFE-750304",
        "fecha": "2024-03-24",
        "ciudad": "GIRARDOT",
        "direccion_entrega": "CRA 50 12 34",
        "subtotal": 52100.0,
        "iva_total": 9899.0,
        "fecha_vto": "20240408",
        "items": [
            {
                "referencia": "90793AQ82100",
                "descripcion": "YAMALUBE",
                "cantidad": 2,
                "valor_total": 52100.0,
                "tiene_iva": True
            }
        ]
    }
