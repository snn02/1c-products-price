# Настройка в IDE

MCP-сервер работает через `stdio`-транспорт — одинаково во всех IDE. Разница только в формате конфиг-файла.

Готовые шаблоны конфигов лежат в папке [`configs/`](../configs/).

---

## Claude Code

Добавьте сервер в `.claude/settings.json` вашего проекта или в глобальный `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "1c-price": {
      "command": "mcp-1c-price",
      "env": {
        "DB_PATH": "/абсолютный/путь/до/data/prices.db"
      }
    }
  }
}
```

Если сервер установлен локально из исходников:

```json
{
  "mcpServers": {
    "1c-price": {
      "command": "uv",
      "args": ["run", "--directory", "/путь/до/1c-products-price", "mcp-1c-price"]
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

## OpenCode (SST)

Добавьте в `opencode.json` в корне проекта:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "1c-price": {
      "type": "local",
      "command": ["mcp-1c-price"],
      "env": {
        "DB_PATH": "/абсолютный/путь/до/data/prices.db"
      }
    }
  }
}
```

Если установлен локально:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "1c-price": {
      "type": "local",
      "command": ["uv", "run", "--directory", "/путь/до/1c-products-price", "mcp-1c-price"]
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
    command: mcp-1c-price
    env:
      DB_PATH: /абсолютный/путь/до/data/prices.db
```

Если установлен локально:

```yaml
mcpServers:
  1c-price:
    command: uv
    args:
      - run
      - --directory
      - /путь/до/1c-products-price
      - mcp-1c-price
```

---

## Переменные окружения

| Переменная | По умолчанию | Описание |
|-----------|-------------|----------|
| `PRICE_URL` | `https://1c.ru/ftp/pub/pricelst/price_1c.zip` | URL прайс-листа |
| `DB_PATH` | `data/prices.db` | Путь к базе данных |
| `AUTO_UPDATE_DAYS` | `1` | Обновлять базу если прайс старше N дней |

Переменные задаются через `.env` файл или в секции `env` конфига IDE.

---

## Проверка работы

После настройки напишите в IDE:

```
покажи что умеешь делать с прайсом 1С
```

AI должен описать доступные инструменты: поиск продуктов, формирование КП, обновление базы.
