import os, argparse, subprocess
from flask import Flask
from flask.ext.restful import Api
from celery import Celery
from nipyper.util import memoize

@memoize
def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery


@memoize
def createApp():
    parser = argparse.ArgumentParser(description='Run a Nipype server.')

    defaults = {
        'DEBUG': True,
        'SECRET_KEY': 'the quick brown fox jumps over the lazy dog',
        'CELERY_BROKER_URL': 'redis://localhost:6379',
        'CELERY_RESULT_BACKEND': 'redis://localhost:6379'
    }

    # define CLI arguments
    # parser.add_argument('-d', '--debug', dest='debug', action='store_const', const=True, default=False, help='run in debug mode')
    # parser.add_argument('-p', '--port', type=str, dest='port', nargs=1, default='5000', help='http port number')
    # parser.add_argument('--broker', type=str, dest='broker', nargs=1, default=defaults['CELERY_BROKER_URL'], help='celery broker url')
    # parser.add_argument('--backend', type=str, dest='backend', nargs=1, default=defaults['CELERY_RESULT_BACKEND'], help='celery result backend url')
    # parser.add_argument('-s', '--secret', type=str, dest='secret', nargs=1, default=defaults['SECRET_KEY'], help='application secret key')
    # args = parser.parse_args()

    config = {}

    for field in defaults.keys():
        try:
            config[field] = os.environ[field]
        except KeyError:
            config[field] = defaults[field]
            # config[field] = {
            #     'SECRET_KEY': args.secret,
            #     'CELERY_BROKER_URL': args.broker,
            #     'CELERY_RESULT_BACKEND': args.backend
            # }[field]

    app = Flask(__name__)
    app.config.update(
        DEBUG = config['DEBUG'],
        SECRET_KEY = config['SECRET_KEY'],
        CELERY_BROKER_URL= config['CELERY_BROKER_URL'],
        CELERY_RESULT_BACKEND = config['CELERY_RESULT_BACKEND'],
    )

    celery = make_celery(app)

    ## create socketIO instance ##
    from flask.ext.socketio import SocketIO
    socketio = SocketIO(app)

    api = Api(app)

    # create directory to store results
    subprocess.call(["mkdir", "results"])

    return app, api, celery, socketio, int(5000)

app, api, celery, socketio, port = createApp()