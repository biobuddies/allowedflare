from ast import literal_eval
from os import getenv
from multiprocessing import cpu_count

access_log_format = '%(r)s st=%(s)s lb=%(h)s ip=%({x-forwarded-for}i)s rt=%(L)ss us=%(u)s rf=%(f)s'
accesslog = '-'
bind = 'localhost:8001'  # Should match docker-compose.yaml and manage.py
reload = bool(literal_eval(getenv('GUNICORN_RELOAD', 'False')))
workers = cpu_count() * 2 + 1
wsgi_app = 'demodj.wsgi'


# Called just before a worker processes the request.
def pre_request(worker, request):
    message = f'{request.method} {request.uri}'
    worker.log.debug(message)
    worker.unfinished_request = message


# Called after a worker processes the request.
def post_request(worker, _request, _environment, _response):
    worker.unfinished_response = ''


# Called when a worker received the SIGABRT signal. This call generally happens on timeout.
def worker_abort(worker):
    if message := getattr(worker, 'unfinished_request'):
        worker.log.critical(f'Interrupted: {message}')
