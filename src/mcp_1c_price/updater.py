import io
import time
import zipfile

import httpx
import xlrd

from . import db, settings


def download() -> bytes:
    """Download price ZIP from 1c.ru and return raw XLS bytes."""
    with httpx.Client(follow_redirects=True, timeout=60) as client:
        response = client.get(settings.PRICE_URL)
        response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        xls_name = next(n for n in zf.namelist() if n.endswith(".xls"))
        return zf.read(xls_name)


def _cell_str(value) -> str:
    """Convert xlrd cell value to clean string (handles float codes like 4601546057532.0)."""
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value).strip()


def _cell_float(value) -> float | None:
    """Return float for numeric cells, None otherwise."""
    return float(value) if isinstance(value, (int, float)) else None


def parse(xls_bytes: bytes) -> tuple[list[dict], str]:
    """Parse XLS bytes → (list of product dicts, price date string)."""
    wb = xlrd.open_workbook(file_contents=xls_bytes)
    sh = wb.sheets()[0]

    # Row 0, col 8: "28 апреля 2026"
    price_date = _cell_str(sh.cell_value(0, 8))

    products: list[dict] = []
    current_section = ""

    for r in range(2, sh.nrows):
        col0 = sh.cell_value(r, 0)
        col1 = sh.cell_value(r, 1)
        col4 = sh.cell_value(r, 4)

        # Section header: text in col 0, empty col 1, contains "Раздел"
        if isinstance(col0, str) and col0.strip() and not str(col1).strip():
            if "Раздел" in col0:
                current_section = col0.strip()
            continue

        # Product row: non-empty code, non-empty name, numeric price
        if not col0 or not col1 or not isinstance(col4, (int, float)):
            continue

        products.append({
            "code":          _cell_str(col0),
            "name":          _cell_str(col1),
            "currency":      _cell_str(sh.cell_value(r, 3)),
            "price_retail":  float(col4),
            "price_dealer":  _cell_float(sh.cell_value(r, 5)),
            "price_partner": _cell_float(sh.cell_value(r, 6)),
            "vat":           _cell_str(sh.cell_value(r, 7)),
            "section":       current_section,
            "date_start":    _cell_str(sh.cell_value(r, 8)),
            "registry":      _cell_str(sh.cell_value(r, 9)),
            "comment":       _cell_str(sh.cell_value(r, 10)),
        })

    return products, price_date


def run() -> dict:
    """Full update cycle: download → parse → save to DB."""
    t0 = time.monotonic()
    db.init_db()
    xls_bytes = download()
    products, price_date = parse(xls_bytes)
    count = db.replace_all(products)
    return {"count": count, "price_date": price_date, "elapsed": time.monotonic() - t0}


def main() -> None:
    print("Скачивание прайс-листа...")
    result = run()
    print(f"Импорт продуктов: {result['count']}")
    print(f"Дата прайса: {result['price_date']}")
    print(f"База обновлена за {result['elapsed']:.1f} сек.")
