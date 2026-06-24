FROM python:3.11-slim

WORKDIR /app

# Сначала зависимости — для использования слоя кэша Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Затем код приложения
COPY src/ ./src/

# Непривилегированный пользователь 
RUN useradd --create-home --shell /bin/bash app \
    && mkdir -p /app/logs \
    && chown -R app:app /app

USER app

# Точка входа: запуск планировщика мониторинга
ENTRYPOINT ["python", "-m", "src.cli"]
CMD ["run"]
