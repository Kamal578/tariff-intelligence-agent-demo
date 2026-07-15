from app.config import get_settings
from app.connectors.router import search_all_sources, source_stats
from app.llm import detect_source_conflict


def test_source_stats_are_mock_only() -> None:
    stats = source_stats(get_settings())

    assert stats["real_connectors_used"] is False
    assert stats["source_counts"] == {"confluence": 10, "wiki": 7, "email": 8}


def test_mock_search_ranks_exact_pack_matches() -> None:
    results = search_all_sources("YouthMax 10GB price", settings=get_settings(), top_k=5)

    assert results
    assert results[0].source_id in {"CONF-001", "MAIL-001"}
    assert any(item.source_id == "CONF-002" for item in results)


def test_source_conflict_detection_for_youthmax() -> None:
    evidence = search_all_sources("YouthMax 10GB price", settings=get_settings(), top_k=6)

    assert detect_source_conflict(evidence)
