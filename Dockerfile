FROM python:3.12-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN git config --global user.name "SDLC-Coding-Agent" && \
    git config --global user.email "agent@itmo-megaschool.local" && \
    git config --global safe.directory /app

# По умолчанию запускаем веб-хук сервер (облако)
# Но GitHub Actions переопределят команду на запуск скриптов
CMD ["uvicorn", "src.webhook_server:app", "--host", "0.0.0.0", "--port", "8000"]
