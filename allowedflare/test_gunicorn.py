from base64 import b64encode
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from gunicorn.app.wsgiapp import WSGIApplication
from gunicorn.http.message import Request
from gunicorn.http.wsgi import Response
from gunicorn.workers.base import Worker
from jwt import encode
from pytest import mark

from allowedflare.gunicorn import local_abort, post_fork, post_request, pre_request


@mark.parametrize(
    ('source', 'email_regex', 'expected_basic', 'expected_jwt', 'validation'),
    [
        ('header', 'off', '-', 'luke@example.com', 'valid'),
        ('cookie', 'off', '-', 'luke@example.com', 'valid'),
        ('header', r'example\.com', '-', 'luke', 'valid'),
        ('basic', 'off', 'leia', '-', 'valid'),
        ('both', 'off', 'leia', 'luke@example.com', 'valid'),
        ('malformed', 'off', '-', 'DecodeError@-', 'valid'),
        ('header', 'off', '-', 'InvalidAudienceError@luke@example.com', 'audience'),
        ('header', 'off', '-', 'ExpiredSignatureError@luke@example.com', 'expiration'),
        ('header', 'off', '-', 'InvalidSignatureError@luke@example.com', 'signature'),
    ],
    ids=(
        'header',
        'cookie',
        'email suffix',
        'basic',
        'basic and jwt',
        'malformed',
        'audience',
        'expiration',
        'signature',
    ),
)
def test_logging(
    source, email_regex, expected_basic, expected_jwt, validation, capsys, mocker, monkeypatch
):
    private_key = generate_private_key(65537, 1024)
    token = (
        'not-a-jwt'
        if source == 'malformed'
        else encode(
            {
                'aud': 'wrong' if validation == 'audience' else 'audience',
                'email': 'luke@example.com',
                'exp': int(
                    datetime.now(UTC).timestamp() + (-1 if validation == 'expiration' else 100)
                ),
            },
            private_key,
            'RS256',
        )
    )
    mocker.patch(
        'allowedflare.core.PyJWKClient.get_signing_key_from_jwt', autospec=True
    ).return_value.key = (
        generate_private_key(65537, 1024).public_key()
        if validation == 'signature'
        else private_key.public_key()
    )
    monkeypatch.setenv('ALLOWEDFLARE_ACCESS_URL', 'https://demo.cloudflareaccess.com')
    monkeypatch.setenv('ALLOWEDFLARE_AUDIENCE', 'audience')
    monkeypatch.setenv('ALLOWEDFLARE_EMAIL_REGEX', email_regex)
    monkeypatch.setattr('sys.argv', ['gunicorn'])
    application = WSGIApplication()
    application.load_config_from_file(str(Path(__file__).parent.parent / 'gunicorn.conf.py'))
    logger = application.cfg.logger_class(application.cfg)
    logger.access(
        mocker.create_autospec(
            Response,
            instance=True,
            status='200',
            response_length=1024,
            sent=1024,
            headers=(('Content-Type', 'text/plain'),),
        ),
        mocker.create_autospec(Request, instance=True, headers=()),
        {
            'REQUEST_METHOD': 'GET',
            'RAW_URI': '/my/path?foo=bar',
            'PATH_INFO': '/my/path',
            'QUERY_STRING': 'foo=bar',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            **(
                {'HTTP_COOKIE': f'CF_Authorization={token}'}
                if source == 'cookie'
                else {'HTTP_AUTHORIZATION': f'Basic {b64encode(b"leia:password").decode()}'}
                if source == 'basic'
                else {
                    'HTTP_AUTHORIZATION': f'Basic {b64encode(b"leia:password").decode()}',
                    'HTTP_CF_ACCESS_JWT_ASSERTION': token,
                }
                if source == 'both'
                else {'HTTP_CF_ACCESS_JWT_ASSERTION': token}
            ),
        },
        timedelta(seconds=1),
    )
    assert capsys.readouterr().out.rstrip() == (
        'GET /my/path?foo=bar HTTP/1.1 st=200 lb=- ip=- rt=1.000000s '
        f'ub={expected_basic} uj={expected_jwt} rf=-'
    )


def test_concurrent_requests_log_only_unfinished_request(capsys, mocker):
    class StandardOutputLogger:
        def critical(self, message):
            print(f'CRITICAL {message}')

        def debug(self, message):
            print(f'DEBUG {message}')

    worker = mocker.create_autospec(Worker, instance=True)
    worker.log = StandardOutputLogger()
    slow_request = mocker.create_autospec(Request, instance=True, method='GET', uri='/sleep/')
    fast_request = mocker.create_autospec(Request, instance=True, method='GET', uri='/admin/login/')
    post_fork(None, worker)

    pre_request(worker, slow_request)
    pre_request(worker, fast_request)
    post_request(worker, fast_request, {}, None)
    local_abort(worker)

    assert worker.unfinished_requests == {}
    assert capsys.readouterr().out.splitlines() == [
        'DEBUG GET /sleep/',
        'DEBUG GET /admin/login/',
        'CRITICAL Interrupted: GET /sleep/',
    ]


def test_unfinished_requests_cleared_after_request(mocker):
    worker = mocker.create_autospec(Worker, instance=True)
    worker.log = mocker.Mock()
    request = mocker.create_autospec(Request, instance=True, method='GET', uri='/health/')
    post_fork(None, worker)

    pre_request(worker, request)
    assert len(worker.unfinished_requests) == 1

    post_request(worker, request, {}, None)
    assert worker.unfinished_requests == {}


def test_unfinished_requests_cleared_after_abort(mocker):
    worker = mocker.create_autospec(Worker, instance=True)
    worker.log = mocker.Mock()
    request = mocker.create_autospec(Request, instance=True, method='GET', uri='/sleep/')
    post_fork(None, worker)

    pre_request(worker, request)
    assert len(worker.unfinished_requests) == 1

    local_abort(worker)
    assert worker.unfinished_requests == {}
