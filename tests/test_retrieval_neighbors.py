from app import retrieval


def _page(document_id: str, number: int) -> dict:
    lecture = int(document_id[3:5])
    return {
        "page_id": f"{document_id}-p{number:03d}",
        "document_id": document_id,
        "lecture": lecture,
        "document_title": f"講義{lecture}",
        "section": "章",
        "title": f"ページ{number}",
        "page": number,
        "content": f"本文{number}",
    }


def test_search_with_neighbors_adds_previous_and_next_pages(monkeypatch):
    pages = [_page("lec02-main", number) for number in range(50, 54)]

    hits = [
        {**pages[2], "distance": 0.10},  # p.52
        {**pages[1], "distance": 0.20},  # p.51
    ]

    monkeypatch.setattr(retrieval, "search", lambda query: hits)
    monkeypatch.setattr(retrieval, "load_pages", lambda source: pages)

    results = retrieval.search_with_neighbors("LoRA QLoRA")

    assert [result["page_id"] for result in results] == [
        "lec02-main-p052",
        "lec02-main-p051",
        "lec02-main-p053",
        "lec02-main-p050",
    ]
    assert len({result["page_id"] for result in results}) == 4
    assert [result["relation"] for result in results[:2]] == ["match", "match"]
    assert [result["relation"] for result in results[2:]] == [
        "neighbor",
        "neighbor",
    ]


def test_search_with_neighbors_does_not_cross_document_boundary(monkeypatch):
    pages = [
        _page("lec01-main", 1),
        _page("lec01-main", 2),
        _page("lec02-main", 1),
        _page("lec02-main", 2),
    ]
    hit = {**pages[1], "distance": 0.10}

    monkeypatch.setattr(retrieval, "search", lambda query: [hit])
    monkeypatch.setattr(retrieval, "load_pages", lambda source: pages)

    results = retrieval.search_with_neighbors("質問")

    assert [result["page_id"] for result in results] == [
        "lec01-main-p002",
        "lec01-main-p001",
    ]
    assert all(result["document_id"] == "lec01-main" for result in results)


def test_search_with_neighbors_rejects_negative_radius():
    try:
        retrieval.search_with_neighbors("質問", radius=-1)
    except ValueError as error:
        assert "0以上の整数" in str(error)
    else:
        raise AssertionError("負のradiusでValueErrorが発生しませんでした")


def test_neighbor_tool_returns_retrieval_results(monkeypatch):
    import json

    from app import tools

    expected = [
        {
            **_page("lec02-main", 52),
            "distance": 0.1,
            "relation": "match",
            "seed_page_id": "lec02-main-p052",
        },
        {
            **_page("lec02-main", 51),
            "distance": None,
            "relation": "neighbor",
            "seed_page_id": "lec02-main-p052",
        },
    ]

    monkeypatch.setattr(
        retrieval,
        "search_with_neighbors",
        lambda query, radius=1: expected,
    )

    result = json.loads(
        tools.search_materials_with_neighbors("LoRA QLoRA")
    )

    assert result["results"] == expected
