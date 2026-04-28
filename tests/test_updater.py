from unittest.mock import MagicMock, patch


def _make_sheet(rows: list[list]) -> MagicMock:
    """Build a mock xlrd sheet from a 2D list of values."""
    sheet = MagicMock()
    sheet.nrows = len(rows)
    sheet.cell_value = lambda r, c: rows[r][c] if c < len(rows[r]) else ""
    return sheet


def _make_workbook(rows: list[list]) -> MagicMock:
    wb = MagicMock()
    wb.sheets.return_value = [_make_sheet(rows)]
    return wb


SAMPLE_ROWS = [
    # Row 0: title
    ["", "Прайс-лист фирмы 1С", "", "", "", "", "", "", "28 апреля 2026", "", ""],
    # Row 1: column headers
    ["Код", "Наименование", "", "Валюта", "Рек. цена", "Дилер", "Партнёр", "НДС", "Дата", "Реестр", "Комментарий"],
    # Row 2: section header
    ["Раздел 1. 1С:ПРЕДПРИЯТИЕ", "", "", "", "", "", "", "", "", "", ""],
    # Row 3: subsection header (no "Раздел", skipped without updating section)
    ["1.1. Программные продукты", "", "", "", "", "", "", "", "", "", ""],
    # Row 4: product with string code
    ["4601546057532", "1С:Бухгалтерия 8. Базовая версия. Электронная поставка",
     "", "руб.", 3600.0, 1800.0, 1620.0, "Без НДС", "01.01.2010", "245", ""],
    # Row 5: product with float code (as Excel sometimes stores barcodes)
    [4601546064462.0, "1С:ERP Управление предприятием 2. Корп",
     "", "руб.", 360000.0, 180000.0, 162000.0, "Без НДС", "01.01.2015", "312", "Комментарий"],
    # Row 6: empty / incomplete row — must be skipped
    ["", "", "", "", "", "", "", "", "", "", ""],
    # Row 7: row with text code but no price — must be skipped
    ["Примечание", "Какой-то текст", "", "", "", "", "", "", "", "", ""],
]


@patch("mcp_1c_price.updater.xlrd.open_workbook")
def test_parse_returns_price_date(mock_open):
    mock_open.return_value = _make_workbook(SAMPLE_ROWS)
    from mcp_1c_price.updater import parse
    _, price_date = parse(b"fake")
    assert price_date == "28 апреля 2026"


@patch("mcp_1c_price.updater.xlrd.open_workbook")
def test_parse_extracts_products(mock_open):
    mock_open.return_value = _make_workbook(SAMPLE_ROWS)
    from mcp_1c_price.updater import parse
    products, _ = parse(b"fake")
    assert len(products) == 2


@patch("mcp_1c_price.updater.xlrd.open_workbook")
def test_parse_skips_section_headers(mock_open):
    mock_open.return_value = _make_workbook(SAMPLE_ROWS)
    from mcp_1c_price.updater import parse
    products, _ = parse(b"fake")
    codes = [p["code"] for p in products]
    assert "Раздел 1. 1С:ПРЕДПРИЯТИЕ" not in codes
    assert "1.1. Программные продукты" not in codes


@patch("mcp_1c_price.updater.xlrd.open_workbook")
def test_parse_skips_rows_without_price(mock_open):
    mock_open.return_value = _make_workbook(SAMPLE_ROWS)
    from mcp_1c_price.updater import parse
    products, _ = parse(b"fake")
    assert all(p["price_retail"] > 0 for p in products)


@patch("mcp_1c_price.updater.xlrd.open_workbook")
def test_parse_float_code_converted_to_string(mock_open):
    mock_open.return_value = _make_workbook(SAMPLE_ROWS)
    from mcp_1c_price.updater import parse
    products, _ = parse(b"fake")
    erp = next(p for p in products if "ERP" in p["name"])
    assert erp["code"] == "4601546064462"
    assert isinstance(erp["code"], str)


@patch("mcp_1c_price.updater.xlrd.open_workbook")
def test_parse_assigns_section(mock_open):
    mock_open.return_value = _make_workbook(SAMPLE_ROWS)
    from mcp_1c_price.updater import parse
    products, _ = parse(b"fake")
    assert all(p["section"] == "Раздел 1. 1С:ПРЕДПРИЯТИЕ" for p in products)


@patch("mcp_1c_price.updater.xlrd.open_workbook")
def test_parse_all_fields_present(mock_open):
    mock_open.return_value = _make_workbook(SAMPLE_ROWS)
    from mcp_1c_price.updater import parse
    products, _ = parse(b"fake")
    required = {"code", "name", "currency", "price_retail", "price_dealer",
                "price_partner", "vat", "section", "date_start", "registry", "comment"}
    for p in products:
        assert required.issubset(p.keys())
