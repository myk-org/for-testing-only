FROM python:3.12-alpine

WORKDIR /app

COPY src/ /app/src/
COPY tests/ /app/tests/

CMD ["python", "--version"]
