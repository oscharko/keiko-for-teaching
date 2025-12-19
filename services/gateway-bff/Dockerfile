# Build from repository root: docker build -t gateway-bff -f services/gateway-bff/Dockerfile .
FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir uv

# Copy pyproject.toml and install dependencies
COPY services/gateway-bff/pyproject.toml ./
RUN uv pip install --system --no-cache .

RUN useradd --create-home --shell /bin/bash appuser

COPY services/gateway-bff/app ./app
COPY services/shared ./shared

# Add app directory to Python path
ENV PYTHONPATH=/app

USER appuser
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

