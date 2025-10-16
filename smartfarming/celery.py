import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartfarming.settings')

app = Celery('smartfarming')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Konfigurasi Celery Beat (Penjadwal)
app.conf.beat_schedule = {
    'check-alarms-every-minute': {
        'task': 'check_and_run_due_alarms',
        'schedule': crontab(minute='*'),
    },
}