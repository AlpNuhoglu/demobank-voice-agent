# demobank-voice-agent

Backend for a Turkish-language voice agent for **Demo Bank**, a fictional bank,
built on ElevenLabs Agents. The agent calls this service through server tools
(webhooks).

> **All data is synthetic.** Names, phone numbers, cards and merchants are
> made up. Seed phone numbers follow an obviously fake pattern
> (`+905550000001` to `+905550000005`). **Never enable a real SMS provider against the seed
> data**: messages would go to whoever owns those numbers.

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)

## Run locally

```bash
cp .env.example .env   # adjust if needed; never commit .env
uv sync
make seed              # create and fill demobank.db
make run               # http://127.0.0.1:8000/health
```

| Command      | What it does                                     |
|--------------|--------------------------------------------------|
| `make run`   | Start the API with auto-reload (uvicorn)          |
| `make seed`  | Reset the DB and load synthetic data              |
| `make test`  | Run pytest (no network or API keys needed)        |
| `make lint`  | `ruff check` and `ruff format --check`            |
| `make format`| Auto-format and auto-fix lint issues              |

### About `make seed`

- **Destructive:** it drops and recreates **all** tables, including anything
  added in later phases such as stored conversations.
- Transactions cover the 30 days before the current Istanbul time, so the
  demo always has recent data. For a reproducible data set, pass a fixed time:
  `uv run python -m scripts.seed --now 2026-10-01T12:00`. The same `--now`
  always gives the same data.

## Layout

```
app/            FastAPI app: config, db, models, schemas, routers/, services/
scripts/        CLI entry points (seed)
tests/          pytest suite (temporary SQLite, no network)
docs/           design notes
```

See [docs/data-model.md](docs/data-model.md) for the data model.
