FROM python:3.11-slim

WORKDIR /app

COPY ./shared /app/shared
COPY ./services/bff-mobile/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./services/bff-mobile .

CMD uvicorn main:app --host 0.0.0.0 --port 8000
