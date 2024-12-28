FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
COPY .env .
COPY cookies.json .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 4750

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "4750", "--reload"] 