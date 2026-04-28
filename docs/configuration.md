# Настройка в IDE

MCP-сервер работает через `stdio`-транспорт — одинаково во всех IDE. Разница только в формате конфиг-файла.

---

## Claude Code

Добавьте в `.claude/settings.json` вашего проекта или в глобальный `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "1c-price": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/snn02/1c-products-price",
        "mcp-1c-price"
      ]
    }
  }
}
```

Проверка: выполните в Claude Code:
```
/mcp
```
В списке должен появиться `1c-price` со статусом connected.

---

## OpenCode

Добавьте в `opencode.json` в корне проекта:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "1c-price": {
      "type": "local",
      "command": [
        "uvx",
        "--from", "git+https://github.com/snn02/1c-products-price",
        "mcp-1c-price"
      ]
    }
  }
}
```

---

## Codex (OpenAI CLI)

Добавьте в `~/.codex/config.yaml`:

```yaml
mcpServers:
  1c-price:
    command: uvx
    args:
      - --from
      - git+https://github.com/snn02/1c-products-price
      - mcp-1c-price
```

---

## Если пакет установлен глобально

Если вы установили пакет через `uv tool install` или `pip install`, используйте более короткий вариант без `uvx`:

**Claude Code:**
```json
{
  "mcpServers": {
    "1c-price": {
      "command": "mcp-1c-price"
    }
  }
}
```

**OpenCode:**
```json
{
  "mcp": {
    "1c-price": {
      "type": "local",
      "command": ["mcp-1c-price"]
    }
  }
}
```

**Codex:**
```yaml
mcpServers:
  1c-price:
    command: mcp-1c-price
```

---

## Переменные окружения

Задаются через `.env` файл в рабочей директории или в секции `env` конфига IDE.

| Переменная | По умолчанию | Описание |
|-----------|-------------|----------|
| `PRICE_URL` | `https://1c.ru/ftp/pub/pricelst/price_1c.zip` | URL прайс-листа |
| `DB_PATH` | `~/.mcp-1c-price/prices.db` | Путь к базе данных |
| `AUTO_UPDATE_DAYS` | `1` | Обновлять базу если прайс старше N дней |

Менять `DB_PATH` нужно только если хотите хранить базу в нестандартном месте.

---

## Проверка работы

После настройки напишите в IDE:

```
покажи что умеешь делать с прайсом 1С
```

AI должен описать доступные инструменты: поиск продуктов, формирование КП, обновление базы.
