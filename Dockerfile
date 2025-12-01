FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
ENV DJANGO_SETTINGS_MODULE=clothing_store.settings
RUN python manage.py collectstatic --noinput
CMD ["sh", "-c", "exec gunicorn clothing_store.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]
