# API runtime image — Phase 1 skeleton
FROM python:3.11-slim

WORKDIR /app

# Install deps first for layer caching
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir .

# App code + configs
COPY src/ src/
COPY config/ config/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
