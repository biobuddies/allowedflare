"""Configure Gunicorn and label its access logs compactly.

st STatus
lb Load Balancer Internet Protocol (IP) address
ip client Internet Protocol (IP) address
rt Request Time in seconds
ub Username for Basic authentication (password not checked)
uj Username/email for JSON Web Token (JWT) authentication (checked and prefixed with Exception@)
rf ReFerrer
"""

from ast import literal_eval
from datetime import timedelta
from http.cookies import SimpleCookie
from multiprocessing import cpu_count
from os import getenv
from typing import Any

from gunicorn.glogging import Logger

from allowedflare.core import authenticate


class UserLogger(Logger):
    """Add j, the validated Cloudflare Access JSON Web Token username, to Gunicorn log atoms.

    Gunicorn's u atom remains the decoded Basic authentication username. A rejected token produces
    `ExceptionClass@email`; an absent token or missing username produces `-`.
    """

    def atoms(
        self, response: Any, request: Any, environ: dict[str, Any], request_time: timedelta
    ) -> dict[str, Any]:
        atoms = super().atoms(response, request, environ, request_time)
        if token := environ.get('HTTP_CF_ACCESS_JWT_ASSERTION') or getattr(
            SimpleCookie(environ.get('HTTP_COOKIE', '')).get('CF_Authorization'), 'value', ''
        ):
            username, exception_class, message, _ = authenticate({'CF_Authorization': token})
            if exception_class:
                atoms['j'] = f'{exception_class.__name__}@{message.rpartition(" email=")[2]}'
            else:
                atoms['j'] = username or '-'
        else:
            atoms['j'] = '-'
        return atoms


access_log_format = (
    '%(r)s st=%(s)s lb=%(h)s ip=%({x-forwarded-for}i)s rt=%(L)ss ub=%(u)s uj=%(j)s rf=%(f)s'
)


def pre_request(worker, request):
    """Called just before a worker processes the request."""
    message = f'{request.method} {request.uri}'
    worker.log.debug(message)
    worker.unfinished_requests[request] = message


def post_request(worker, request, _environment, _response):
    """Called after a worker processes the request."""
    worker.unfinished_requests.pop(request, None)


def post_fork(_server, worker):
    """Initialize request state in each worker process."""
    worker.unfinished_requests = {}


def local_abort(worker):
    """Called when a worker received the SIGABRT signal. This call generally happens on timeout."""
    for message in tuple(worker.unfinished_requests.values()):
        worker.log.critical(f'Interrupted: {message}')


def configure(namespace):
    namespace.update(
        access_log_format=access_log_format,
        accesslog='-',
        logging_class=UserLogger,
        post_fork=post_fork,
        post_request=post_request,
        pre_request=pre_request,
        reload=bool(literal_eval(getenv('GUNICORN_RELOAD', 'False'))),
        worker_abort=local_abort,
        workers=cpu_count() * 2 + 1,
    )
