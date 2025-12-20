# Build from repository root: docker build -t ideas-service -f services/ideas-service/Dockerfile .
FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir uv

# Install dependencies directly
RUN uv pip install --system --no-cache \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.30.0" \
    "pydantic>=2.9.0" \
    "pydantic-settings>=2.5.0" \
    "azure-cosmos>=4.8.0" \
    "azure-search-documents>=11.4.0" \
    "azure-identity>=1.18.0" \
    "openai>=1.47.0" \
    "python-multipart>=0.0.12" \
    "httpx>=0.27.0"

RUN useradd --create-home --shell /bin/bash appuser

COPY services/ideas-service/app ./app
COPY services/shared ./shared

ENV PYTHONPATH=/app

USER appuser
EXPOSE 8007

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8007"]
