# this is a hack to allow Celery to discover the celery instance

from nipyper.app import celery as cel
celery = cel