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

# e2e: uncacheable slow layer to open a duplicate/supersede window
RUN date +%s%N > /tmp/e2e-stamp && sleep 120
