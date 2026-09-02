from base64 import b64encode
from datetime import UTC, datetime, timedelta
from pathlib import Path
from socket import create_connection, socket
from subprocess import PIPE, STDOUT, Popen
from sys import executable
from time import monotonic, sleep

from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from requests import get
from requests.exceptions import RequestException

from allowedflare.gunicorn import UserLogger, access_log_format
from gunicorn.config import Config
from gunicorn.http.message import Request
from gunicorn.http.wsgi import Response
from jwt import encode
from pytest import mark


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
def test_get_basic_and_jwt_usernames(
    source, email_regex, expected_basic, expected_jwt, validation, mocker, monkeypatch
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
    assert (
        UserLogger(Config())
        .atoms(
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
        .items()
        >= {'u': expected_basic, 'j': expected_jwt}.items()
    )


def test_access_log_labels_basic_and_jwt_users():
    assert 'ub=%(u)s uj=%(j)s' in access_log_format


def test_timeout_then_response_logs_independent_requests():
    with socket() as reserved_socket:
        reserved_socket.bind(('127.0.0.1', 0))
        port = reserved_socket.getsockname()[1]

    process = Popen(
        [
            str(Path(executable).with_name('gunicorn')),
            '--bind',
            f'127.0.0.1:{port}',
            '--config',
            str(Path(__file__).parents[1] / 'gunicorn.conf.py'),
            '--timeout',
            '1',
            '--workers',
            '1',
            'demodj.wsgi',
        ],
        stdout=PIPE,
        stderr=STDOUT,
        text=True,
    )
    try:
        deadline = monotonic() + 10
        while True:
            try:
                with create_connection(('127.0.0.1', port), timeout=0.1):
                    pass
                break
            except OSError:
                if monotonic() >= deadline:
                    raise
                sleep(0.05)

        try:
            get(f'http://127.0.0.1:{port}/sleep/', timeout=5)
        except RequestException:
            pass

        while True:
            try:
                response = get(f'http://127.0.0.1:{port}/admin/login/', timeout=1)
                break
            except RequestException:
                if monotonic() >= deadline:
                    raise
                sleep(0.05)
    finally:
        process.terminate()
        stdout = process.communicate(timeout=5)[0]

    assert response.status_code == 200
    assert 'Interrupted: GET /sleep/' in stdout
    assert 'GET /admin/login/ HTTP/1.1 st=200' in stdout
    assert 'Interrupted: GET /admin/login/' not in stdout
