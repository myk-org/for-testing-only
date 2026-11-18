FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
COPY tests/ tests/

RUN python -c "import time; time.sleep(25)"
RUN pip install --no-cache-dir -e ".[dev]"

EXPOSE 8000

CMD ["taskflow", "server", "--port", "8000"]
