import pytest
from pathlib import Path

SAMPLE_PRODUCTS = [
    {
        "code": "4601546057532",
        "name": "1С:Бухгалтерия 8. Базовая версия. Электронная поставка",
        "currency": "руб.",
        "price_retail": 3600.0,
        "price_dealer": 1800.0,
        "price_partner": 1620.0,
        "vat": "Без НДС",
        "section": "Раздел 1. 1С:ПРЕДПРИЯТИЕ",
        "date_start": "01.01.2010",
        "registry": "245",
        "comment": "",
    },
    {
        "code": "4601546064462",
        "name": "1С:ERP Управление предприятием 2. Корп",
        "currency": "руб.",
        "price_retail": 360000.0,
        "price_dealer": 180000.0,
        "price_partner": 162000.0,
        "vat": "Без НДС",
        "section": "Раздел 1. 1С:ПРЕДПРИЯТИЕ",
        "date_start": "01.01.2015",
        "registry": "312",
        "comment": "",
    },
]


@pytest.fixture(autouse=True)
def fresh_db(monkeypatch):
    """Each test gets a clean in-memory SQLite — no file, no state leak."""
    import mcp_1c_price.settings as s
    import mcp_1c_price.db as db_module

    monkeypatch.setattr(s, "DB_PATH", Path(":memory:"))
    db_module._conn = None

    yield

    if db_module._conn:
        db_module._conn.close()
        db_module._conn = None


def test_init_db():
    from mcp_1c_price import db
    db.init_db()
    assert db.meta()["count"] == 0


def test_replace_all_returns_count():
    from mcp_1c_price import db
    db.init_db()
    assert db.replace_all(SAMPLE_PRODUCTS) == 2


def test_replace_all_persists():
    from mcp_1c_price import db
    db.init_db()
    db.replace_all(SAMPLE_PRODUCTS)
    assert db.meta()["count"] == 2


def test_replace_all_clears_previous_data():
    from mcp_1c_price import db
    db.init_db()
    db.replace_all(SAMPLE_PRODUCTS)
    db.replace_all([SAMPLE_PRODUCTS[0]])
    assert db.meta()["count"] == 1


def test_search_fts_finds_product():
    from mcp_1c_price import db
    db.init_db()
    db.replace_all(SAMPLE_PRODUCTS)
    results = db.search("бухгалтерия")
    assert len(results) >= 1
    assert any("Бухгалтерия" in r["name"] for r in results)


def test_search_fts_finds_erp():
    from mcp_1c_price import db
    db.init_db()
    db.replace_all(SAMPLE_PRODUCTS)
    results = db.search("ERP управление")
    assert len(results) >= 1
    assert any("ERP" in r["name"] for r in results)


def test_search_like_fallback():
    from mcp_1c_price import db
    db.init_db()
    db.replace_all(SAMPLE_PRODUCTS)
    # Phrase with stopword-like tokens that FTS might skip — LIKE must catch it
    results = db.search("Базовая версия")
    assert len(results) >= 1


def test_search_returns_empty_for_unknown():
    from mcp_1c_price import db
    db.init_db()
    db.replace_all(SAMPLE_PRODUCTS)
    assert db.search("продуктнесуществующий_xyz999") == []


def test_get_by_code_found():
    from mcp_1c_price import db
    db.init_db()
    db.replace_all(SAMPLE_PRODUCTS)
    p = db.get_by_code("4601546057532")
    assert p is not None
    assert p["price_retail"] == 3600.0
    assert p["currency"] == "руб."


def test_get_by_code_not_found():
    from mcp_1c_price import db
    db.init_db()
    db.replace_all(SAMPLE_PRODUCTS)
    assert db.get_by_code("0000000000000") is None
