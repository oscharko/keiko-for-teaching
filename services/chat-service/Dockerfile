# Build from repository root: docker build -t chat-service -f services/chat-service/Dockerfile .
FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir uv

# Install dependencies directly
RUN uv pip install --system --no-cache \
    "fastapi>=0.115.6" \
    "uvicorn[standard]>=0.34.0" \
    "httpx>=0.28.1" \
    "azure-ai-projects>=1.0.0b1" \
    "azure-ai-inference>=1.0.0b5" \
    "openai>=1.58.1" \
    "azure-identity>=1.19.0" \
    "redis>=5.2.1" \
    "pydantic>=2.10.3" \
    "pydantic-settings>=2.7.0" \
    "tiktoken>=0.8.0" \
    "opentelemetry-api>=1.29.0" \
    "opentelemetry-sdk>=1.29.0" \
    "opentelemetry-instrumentation-fastapi>=0.50b0"

RUN useradd --create-home --shell /bin/bash appuser

COPY services/chat-service/app ./app
COPY services/shared ./shared

ENV PYTHONPATH=/app

USER appuser
EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

