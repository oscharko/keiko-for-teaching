# Build from repository root: docker build -t gateway-bff -f services/gateway-bff/Dockerfile .
FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir uv

# Install dependencies directly
RUN uv pip install --system --no-cache \
    "fastapi>=0.115.6" \
    "uvicorn[standard]>=0.34.0" \
    "httpx>=0.28.1" \
    "azure-identity>=1.19.0" \
    "redis>=5.2.1" \
    "pydantic>=2.10.3" \
    "pydantic-settings>=2.7.0" \
    "python-multipart>=0.0.19" \
    "opentelemetry-api>=1.29.0" \
    "opentelemetry-sdk>=1.29.0" \
    "opentelemetry-instrumentation-fastapi>=0.50b0"

RUN useradd --create-home --shell /bin/bash appuser

# Copy application code
COPY services/gateway-bff/app ./app
COPY services/shared ./shared

# Add app directory to Python path
ENV PYTHONPATH=/app

USER appuser
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

