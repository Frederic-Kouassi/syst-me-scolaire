# students/tasks.py
from celery import shared_task

@shared_task
def index(x, y):
    return x + y
