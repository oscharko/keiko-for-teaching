# Build from repository root: docker build -t news-service -f services/news-service/Dockerfile .
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
    "openai>=1.47.0" \
    "httpx>=0.27.0" \
    "apscheduler>=3.10.4"

RUN useradd --create-home --shell /bin/bash appuser

COPY services/news-service/app ./app
COPY services/shared ./shared

ENV PYTHONPATH=/app

USER appuser
EXPOSE 8006

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8006"]
