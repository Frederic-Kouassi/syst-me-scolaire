# gestion_etudiant/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_etudiant.settings")

app = Celery("gestion_etudiant")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()  # <- indispensable pour que Celery voit vos tâches

@app.task(bind=True, ignore_result= True )
def debug_task(self):
    print(f"request : {self.request}")