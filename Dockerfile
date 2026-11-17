FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
COPY tests/ tests/

RUN pip install --no-cache-dir -e ".[dev]"

EXPOSE 8000

CMD ["taskflow", "server", "--port", "8000"]

# e2e: slow layer so duplicate/supersede paths can be observed
RUN sleep 45
