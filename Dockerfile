# FrankoLab · plan converter + patient cabinet
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    DATA_DIR=/tmp/frankolab-plans

WORKDIR /app

# dependencies first, so code changes rebuild in seconds
COPY requirements.txt /tmp/req/requirements.txt
COPY web/requirements.txt /tmp/req/web.txt
RUN pip install --no-cache-dir -r /tmp/req/requirements.txt -r /tmp/req/web.txt \
 && python -m playwright install --with-deps chromium \
 && rm -rf /var/lib/apt/lists/* /root/.cache

COPY . .
RUN useradd --create-home app && mkdir -p "$DATA_DIR" && chown -R app "$DATA_DIR"
USER app

EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn web.app:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --proxy-headers --forwarded-allow-ips='*'"]
