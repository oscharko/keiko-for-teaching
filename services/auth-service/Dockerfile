# Build from repository root: docker build -t auth-service -f services/auth-service/Dockerfile .
FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir uv

# Copy pyproject.toml and install dependencies
COPY services/auth-service/pyproject.toml ./
RUN uv pip install --system --no-cache .

RUN useradd --create-home --shell /bin/bash appuser

COPY services/auth-service/app ./app
COPY services/shared ./shared

ENV PYTHONPATH=/app

USER appuser
EXPOSE 8004

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]

