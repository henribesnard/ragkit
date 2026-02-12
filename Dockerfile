FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY pyproject.toml README.md LICENSE /app/
COPY ragkit /app/ragkit
COPY templates /app/templates

RUN pip install --no-cache-dir .

EXPOSE 8000 8080

CMD ["python", "-m", "ragkit", "serve", "--config", "/app/ragkit.yaml"]
