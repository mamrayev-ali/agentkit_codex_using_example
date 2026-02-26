FROM python:3.13-slim

WORKDIR /app

RUN python -m pip install --no-cache-dir uv

COPY services/api/ /app/
RUN uv sync --frozen --no-dev

ENV PYTHONPATH=/app/src

CMD ["uv", "run", "--frozen", "uvicorn", "decider_api.app:app", "--host", "0.0.0.0", "--port", "8000"]
