import pytest
from backend.core.query_router import QueryRouter
from backend.models.schemas import Classification

@pytest.mark.unit
def test_classify_query_understanding_off():
    """When query_understanding=False -> always FACT, top_k=5."""
    res = QueryRouter.classify("Any query here vs that query", query_understanding=False)
    assert res.type == "FACT"
    assert res.top_k == 5
    assert res.sub_queries is None

@pytest.mark.unit
def test_classify_fact_short_question():
    """<=8 words ending with '?' -> FACT, top_k=3."""
    res = QueryRouter.classify("What is error E452?", query_understanding=True)
    assert res.type == "FACT"
    assert res.top_k == 3
    assert res.sub_queries is None

@pytest.mark.unit
def test_classify_topic_long_question():
    """Long queries without compare keywords -> TOPIC, top_k=7."""
    res = QueryRouter.classify("Explain the complete maintenance procedure for industrial servers in the facility", query_understanding=True)
    assert res.type == "TOPIC"
    assert res.top_k == 7
    assert res.sub_queries is None

@pytest.mark.unit
def test_classify_compare_vs():
    """Query containing 'vs' -> COMPARE with sub_queries."""
    res = QueryRouter.classify("server units vs industrial routers", query_understanding=True)
    assert res.type == "COMPARE"
    assert res.top_k == 5
    assert res.sub_queries == ["server units", "industrial routers"]

@pytest.mark.unit
def test_classify_compare_difference_between():
    """Query with 'difference between' -> COMPARE."""
    res = QueryRouter.classify("What is the difference between E452 and E501?", query_understanding=True)
    assert res.type == "COMPARE"
    assert res.top_k == 5
    assert res.sub_queries == ["E452", "E501?"] # regex group extracts remainder including '?'

@pytest.mark.unit
def test_extract_compare_entities():
    """Verify entity extraction helper."""
    entities = QueryRouter.extract_compare_entities("E452 versus E501")
    assert entities == ["E452", "E501"]
    
    entities = QueryRouter.extract_compare_entities("gateway compared to controller")
    assert entities == ["gateway", "controller"]

@pytest.mark.unit
def test_extract_compare_entities_no_split():
    """Query with compare keyword but no clear split -> returns original clean string."""
    entities = QueryRouter.extract_compare_entities("just compare")
    assert entities == ["just compare"]
