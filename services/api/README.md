# Decider API (T2 scaffold)

Minimal backend scaffold for ticket T2.

## Run

```powershell
uv run --directory services/api uvicorn decider_api.app:app --host 0.0.0.0 --port 8000
```

## Test

```powershell
uv run --directory services/api pytest -q -m smoke
uv run --directory services/api pytest -q
```
