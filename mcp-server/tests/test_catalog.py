from iec_mcp import catalog


def test_search_products_finds_switch():
    results = catalog.search_products("NS-SW")
    assert any(item["model_number"] == "NS-SW-005" for item in results)


def test_validate_voltage_pass():
    result = catalog.validate_requirement("NS-SW-005", "supply_voltage_v", ">=", "24")
    assert result["status"] == "PASS"


def test_quote_draft_total():
    draft = catalog.create_quote_draft("NS-SW-005", 10)
    assert draft["total"] == "1850.00"
    assert draft["requires_human_approval"] is True
