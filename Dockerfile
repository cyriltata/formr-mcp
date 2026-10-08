FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FORMR_MCP_PORT=3001

WORKDIR /app

RUN useradd --create-home --uid 1000 --user-group app

COPY pyproject.toml ./
COPY formr_mcp ./formr_mcp
COPY docker/entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir . \
    && chmod 755 /entrypoint.sh

USER app

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('FORMR_MCP_PORT','3001'))"

ENTRYPOINT ["/entrypoint.sh"]
