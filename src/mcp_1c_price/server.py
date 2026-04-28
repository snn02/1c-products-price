from pydantic import BaseModel
from fastmcp import FastMCP

from . import db, updater

db.init_db()


def _fmt(value: float) -> str:
    """Format price as '3 600 ₽' with space thousands separator."""
    return f"{value:,.0f}".replace(",", " ") + " ₽"


mcp = FastMCP(
    "1c-price",
    instructions="""You are a 1C software pricing assistant for sales managers.
When a user describes products they need (in any form or language), follow these steps:
1. Call search_products() for each product or product group mentioned — even vague ones.
2. If a match is ambiguous, list top options and ask the user to clarify.
3. Once products and quantities are confirmed, call build_quote() with codes and quantities.
4. If search returns no results for any query, call refresh_prices() first, then retry.
Always respond in Russian.""",
)


class QuoteItem(BaseModel):
    code: str
    qty: int = 1


@mcp.tool()
def search_products(query: str, limit: int = 10) -> list[dict]:
    """Search 1C software products by name or free-form description.
    Call this for every product or category the user mentions before building a quote.
    Returns list of {code, name, price_retail, currency, vat, section}."""
    return db.search(query, limit)


@mcp.tool()
def get_product(code: str) -> dict | None:
    """Get full details of a 1C product by its exact 13-digit article code."""
    return db.get_by_code(code)


@mcp.tool()
def build_quote(items: list[QuoteItem]) -> str:
    """Build a formatted commercial quote (КП) from a list of {code, qty} items.
    Use codes returned by search_products. qty defaults to 1.
    Returns a markdown table with names, unit prices, quantities and total sum."""
    rows: list[str] = []
    total = 0.0
    warnings: list[str] = []

    for i, item in enumerate(items, 1):
        product = db.get_by_code(item.code)
        if not product:
            warnings.append(f"⚠️ Код {item.code} не найден в базе")
            rows.append(f"| {i} | {item.code} | ⚠️ Не найден | {item.qty} | — | — |")
            continue

        price = product["price_retail"] or 0.0
        amount = price * item.qty
        total += amount

        name = product["name"]
        if len(name) > 55:
            name = name[:52] + "..."

        rows.append(
            f"| {i} | `{product['code']}` | {name} | {item.qty} "
            f"| {_fmt(price)} | {_fmt(amount)} |"
        )

    header = (
        "| № | Код | Наименование | Кол-во | Цена | Сумма |\n"
        "|---|-----|--------------|-------:|-----:|------:|"
    )
    footer = f"|   |     | **ИТОГО**    |        |      | **{_fmt(total)}** |"

    parts = [header] + rows + [footer]
    if warnings:
        parts += [""] + warnings

    return "\n".join(parts)


@mcp.tool()
def refresh_prices() -> str:
    """Download and reimport the latest 1C price list from 1c.ru.
    Call when the user asks to update prices, or when search returns no results."""
    result = updater.run()
    return (
        f"Прайс-лист обновлён.\n"
        f"Дата прайса: {result['price_date']}\n"
        f"Загружено продуктов: {result['count']}\n"
        f"Время обновления: {result['elapsed']:.1f} сек."
    )
