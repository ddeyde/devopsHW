# образ с Linux и Python 3.11
FROM python:3.11-slim

# Создаем рабчую папку 
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

#порт, который слушает приложение
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
