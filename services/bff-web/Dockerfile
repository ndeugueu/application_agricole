FROM python:3.11-slim

WORKDIR /app

COPY ./shared /app/shared
COPY ./services/bff-web/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./services/bff-web .

CMD uvicorn main:app --host 0.0.0.0 --port 8000
