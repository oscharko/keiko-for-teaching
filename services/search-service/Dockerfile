# Build from repository root: docker build -t search-service -f services/search-service/Dockerfile .
FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir uv

# Install dependencies directly
RUN uv pip install --system --no-cache \
    "fastapi>=0.115.6" \
    "uvicorn[standard]>=0.34.0" \
    "httpx>=0.28.1" \
    "aiohttp>=3.10.0" \
    "azure-identity>=1.19.0" \
    "azure-search-documents>=11.6.0" \
    "redis>=5.2.1" \
    "pydantic>=2.10.3" \
    "pydantic-settings>=2.7.0" \
    "opentelemetry-api>=1.29.0" \
    "opentelemetry-sdk>=1.29.0" \
    "opentelemetry-instrumentation-fastapi>=0.50b0"

RUN useradd --create-home --shell /bin/bash appuser

COPY services/search-service/app ./app
COPY services/shared ./shared

ENV PYTHONPATH=/app

USER appuser
EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]

