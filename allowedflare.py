import logging
from datetime import datetime, timedelta
from datetime import timezone
from http.cookies import Morsel
from os import environ, getenv

import requests
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from jwt import DecodeError, InvalidSignatureError, decode
from jwt.algorithms import RSAAlgorithm

cache_updated = datetime.fromtimestamp(0, tz=timezone.utc)
cached_keys: list[RSAPublicKey] = []
logger = logging.getLogger(__name__)


def clean_username(username: str) -> str:
    """
    Remove @{suffix} from username, where suffix is `settings.ALLOWEDFLARE_EMAIL_DOMAIN` or
    `settings.ALLOWEDFLARE_PRIVATE_DOMAIN`. Set `ALLOWEDFLARE_EMAIL_DOMAIN=off` to leave the
    username unmodified.

    Compared to `RemoteUserBackend.clean_username()`, the `self` argument is omitted to make
    user-provided replacement easier.
    """
    suffix = getenv(
        getenv('ALLOWEDFLARE_EMAIL_DOMAIN', getenv('ALLOWEDFLARE_PRIVATE_DOMAIN', 'off'))
    )
    return username.removesuffix(f'@{suffix}')


def fetch_or_reuse_keys() -> list[RSAPublicKey]:
    global cache_updated, cached_keys  # noqa: PLW0603
    now = datetime.now(tz=timezone.utc)
    # As of June 2023, signing keys are documented as rotated every 6 weeks
    if cache_updated + timedelta(days=1) < now:
        url = getenv('ALLOWEDFLARE_ACCESS_URL', 'off')
        if url == 'off':
            return []
        response = requests.get(f'{url}/cdn-cgi/access/certs', timeout=3).json()
        if response.get('keys'):
            rsa_public_keys = []
            for key in response['keys']:
                decoded_key = RSAAlgorithm.from_jwk(key)
                if isinstance(decoded_key, RSAPublicKey):
                    rsa_public_keys.append(decoded_key)
            if rsa_public_keys:
                cached_keys = rsa_public_keys
                cache_updated = now
    return cached_keys


def decode_token(cf_authorization: str) -> dict:
    if getenv('ALLOWEDFLARE_ACCESS_URL', 'off') == 'off':
        return {}
    for key in fetch_or_reuse_keys():
        try:
            return decode(
                cf_authorization,
                key=key,
                audience=environ['ALLOWEDFLARE_AUDIENCE'],
                algorithms=['RS256'],
            )
        except (DecodeError, InvalidSignatureError):
            pass
    return {}


def authenticate(cookies: dict[str, Morsel | str]) -> tuple[str, str, dict]:
    """
    Return a tuple with suffix-trimmed username, failure/success message, and decoded token.

    On failure to authenticate, the username will be the empty string `''` and the token will be the
    empty dictionary `{}`.
    """
    if getenv('ALLOWEDFLARE_ACCESS_URL', 'off') == 'off':
        return ('', 'Allowedflare is off', {})

    if 'CF_Authorization' not in cookies:
        return ('', 'Allowedflare could not find CF_Authorization cookie', {})
    morsel_or_value = cookies['CF_Authorization']
    if isinstance(morsel_or_value, Morsel):
        cookie = morsel_or_value.value
    else:
        cookie = morsel_or_value
    token = decode_token(cookie)
    if not token:
        return ('', f'Allowedflare found invalid CF_Authorization cookie {cookie}', {})
    if 'email' not in token:
        return ('', f'Allowedflare could not find email within otherwise valid token {token}', {})

    cleaned_username = clean_username(token['email'])
    return (cleaned_username, f'Allowedflare authenticated {cleaned_username}', token)
