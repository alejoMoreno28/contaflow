import pytest

from yamaha_rules import (
    DESCONTABLE,
    EXCLUDED_OILS,
    IVA_MAYOR_COSTO,
    YamahaRuleError,
    calcular_cta_inv,
    enrich_catalog_with_known_oils,
    resolve_tax_treatment,
)


def test_accounts_preserve_002_and_support_003_0001():
    assert calcular_cta_inv("0020001000001") == "1435010201"
    assert calcular_cta_inv("0020077000625") == "1435010277"
    assert calcular_cta_inv("0030001000122") == "1435020101"


def test_account_rule_fails_closed_for_unknown_product_families():
    with pytest.raises(YamahaRuleError, match="sin regla contable"):
        calcular_cta_inv("0040001000001")

    with pytest.raises(YamahaRuleError, match="13 digitos"):
        calcular_cta_inv("003000100012")


def test_approved_excluded_oils_are_complete_and_unique():
    assert len(EXCLUDED_OILS) == 28
    assert len({oil.producto for oil in EXCLUDED_OILS.values()}) == 28
    assert all(oil.producto.startswith("0030001") for oil in EXCLUDED_OILS.values())
    assert EXCLUDED_OILS["90793AV50100"].producto == "0030001000116"
    assert EXCLUDED_OILS["90793AV50400"].producto == "0030001000122"
    assert EXCLUDED_OILS["3374650255668"].producto == "0030001000121"


def test_tax_treatment_is_explicit_for_unknown_003_products():
    assert resolve_tax_treatment("", "90793AV50400", "0030001000122") == IVA_MAYOR_COSTO
    assert resolve_tax_treatment("", "NORMAL002", "0020001000001") == DESCONTABLE
    assert resolve_tax_treatment("", "NUEVO003", "0030001000999") is None
    assert resolve_tax_treatment(DESCONTABLE, "NUEVO003", "0030001000999") == DESCONTABLE


def test_enrichment_protects_known_oils_and_preserves_other_catalog_rows():
    original = {
        "REPUESTO002": {
            "producto": "0020001000001",
            "cta_inv": "1435010201",
        },
        "90793AV50400": {
            "producto": "0030001000122",
            "cta_inv": "1435010201",
        },
    }

    enriched = enrich_catalog_with_known_oils(original)

    assert enriched["REPUESTO002"] == original["REPUESTO002"]
    assert enriched["90793AV50400"]["cta_inv"] == "1435020101"
    assert enriched["90793AV50400"]["tratamiento_iva"] == IVA_MAYOR_COSTO
    assert enriched["90793AV50100"]["producto"] == "0030001000116"
    assert original["90793AV50400"]["cta_inv"] == "1435010201"


def test_enrichment_rejects_a_product_conflict_instead_of_hiding_it():
    catalog = {
        "90793AV50400": {
            "producto": "0030001000999",
            "cta_inv": "1435010201",
        }
    }

    with pytest.raises(YamahaRuleError, match="conflicto"):
        enrich_catalog_with_known_oils(catalog)
