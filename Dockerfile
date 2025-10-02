# Stage ini menginstal dependensi sistem dan Python
FROM python:3.13-slim as builder
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage ini adalah image akhir yang ramping, aman, dan siap produksi.
FROM python:3.13-slim as final
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*
RUN addgroup --system app && adduser --system --group appuser
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .
RUN python manage.py collectstatic --noinput
RUN chown -R appuser:app /app
USER appuser
EXPOSE 8000

# PILIH SALAH SATU
# CMD ["gunicorn", "smartfarming.wsgi:application", "--bind", "0.0.0.0:8000", "--workers=3", "--timeout=30"]
# CMD ["gunicorn", "smartfarming.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "smartfarming.asgi:application"]