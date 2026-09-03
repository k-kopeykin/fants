# Базовый образ: легкий Python 3.12
FROM python:3.12-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения
COPY ./app ./app

# Создаем папку для uploads внутри контейнера
RUN mkdir -p /app/static/uploads

# Открываем порт 8000
EXPOSE 8000

# Команда запуска
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]