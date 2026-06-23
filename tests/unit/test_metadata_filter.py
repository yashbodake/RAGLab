import pytest
from backend.core.retrieval import extract_metadata_filter, matches_filter

@pytest.mark.unit
def test_extract_error_code():
    """'Fix E452' -> {'error_code': 'E452'}."""
    f = extract_metadata_filter("How to resolve E452?")
    assert f == {"error_code": "E452"}
    
    # Lowercase test
    f = extract_metadata_filter("fix error e305 on gateway")
    # Note: e305 normalized to E305. The gateway is a product, so we expect $and
    assert "$and" in f

@pytest.mark.unit
def test_extract_product():
    """'server troubleshooting' -> {'product': 'server'}."""
    f = extract_metadata_filter("troubleshooting server units")
    assert f == {"product": "server"}

@pytest.mark.unit
def test_extract_combined():
    """'E452 on server' -> {'$and': [{'error_code':'E452'}, {'product':'server'}]}."""
    f = extract_metadata_filter("E452 fault on switch")
    assert f == {"$and": [{"error_code": "E452"}, {"product": "switch"}]}

@pytest.mark.unit
def test_extract_no_entities():
    """Generic query -> None."""
    f = extract_metadata_filter("Explain the standard procedure.")
    assert f is None

@pytest.mark.unit
def test_matches_filter():
    """Verify matches_filter helper logic."""
    meta = {"product": "server", "error_code": "E452", "source": "maintenance_manual"}
    
    # Matching cases
    assert matches_filter(meta, {"product": "server"})
    assert matches_filter(meta, {"$and": [{"product": "server"}, {"error_code": "E452"}]})
    assert matches_filter(meta, None)
    
    # Non-matching cases
    assert not matches_filter(meta, {"product": "router"})
    assert not matches_filter(meta, {"$and": [{"product": "server"}, {"error_code": "E501"}]})
