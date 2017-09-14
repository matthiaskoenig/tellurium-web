"""
Celery task management.

http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html#using-celery-with-django
https://realpython.com/blog/python/asynchronous-tasks-with-django-and-celery/

"""
from __future__ import absolute_import, unicode_literals
import os
# from . import settings
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'teweb.settings')

app = Celery('teweb')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')  # celery 4
# app.config_from_object('django.conf:settings')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()  # celery 4
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

