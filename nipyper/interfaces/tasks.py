from nipyper.app import celery as app
from celery import task
from celery.app import app_or_default
app = app_or_default(app)

from .registry import registry as interfaces

@app.task()
def resolve(name):
    interface, isInterface = interfaces.resolve(name)
    return interface, isInterface