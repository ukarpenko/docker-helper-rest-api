#minio-client:2.0
# Используем официальный образ с Python (или другой базовый образ)
FROM python:3.9-slim

# Устанавливаем необходимые утилиты (например, AWS CLI)
RUN apt-get update && apt-get install -y awscli curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем MinIO клиент (mc)
RUN curl -sSL https://dl.min.io/client/mc/release/linux-amd64/mc > /usr/local/bin/mc
RUN chmod +x /usr/local/bin/mc

# Устанавливаем зависимости для FastAPI
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения в контейнер
COPY . /app/

# Указываем, что приложение будет слушать на порту 8000
EXPOSE 8000

# Запускаем FastAPI с использованием uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
