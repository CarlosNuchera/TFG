
from __future__ import absolute_import, unicode_literals
import os
from celery.schedules import crontab
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tfg.settings')

app = Celery('tfg')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.broker_connection_retry_on_startup = True
app.conf.update(timezone = 'Europe/Spain')

#Celery Beat Settings
app.conf.beat_schedule = {
    'actualizar-datos': {
        'task': 'esios.tasks.actualizar_datos_automaticamente',
        'schedule': crontab(hour=0, minute=0)
    }
}

app.autodiscover_tasks()
