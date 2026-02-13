FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY . /app
ENV DJANGO_SETTINGS_MODULE=clothing_store.settings
CMD ["sh", "-c", "python manage.py migrate --noinput || true; python manage.py collectstatic --noinput || true; exec gunicorn clothing_store.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 2 --timeout 90 --access-logfile - --error-logfile - --capture-output"]
