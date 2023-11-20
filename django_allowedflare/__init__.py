import logging
from datetime import datetime, timedelta, timezone as datetime_timezone
from typing import Any

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.utils import timezone as django_utils_timezone
from django.conf import settings
from jwt.algorithms import RSAAlgorithm
from jwt import decode, InvalidSignatureError
import requests


cache_updated = datetime.fromtimestamp(0, tz=datetime_timezone.utc)
cached_keys: list[RSAPublicKey] = []
logger = logging.getLogger(__name__)


def clean_username(username: str) -> str:
    return username.removesuffix(f'@{settings.ALLOWEDFLARE_PRIVATE_DOMAIN}')


def fetch_or_reuse_keys() -> list[RSAPublicKey]:
    global cache_updated, cached_keys
    now = django_utils_timezone.now()
    # As of June 2023, signing keys are documented as rotated every 6 weeks
    if cache_updated + timedelta(days=1) < now:
        response = requests.get(f'{settings.ALLOWEDFLARE_ACCESS_URL}/cdn-cgi/access/certs').json()
        if response.get('keys'):
            decoded_keys = [RSAAlgorithm.from_jwk(key) for key in response['keys']]
            cached_keys = [key for key in decoded_keys if isinstance(key, RSAPublicKey)]
            cache_updated = now
    return cached_keys


def decode_token(cf_authorization: str) -> dict:
    for key in fetch_or_reuse_keys():
        try:
            return decode(
                cf_authorization,
                key=key,
                audience=settings.ALLOWEDFLARE_AUDIENCE,
                algorithms=['RS256'],
            )
        except InvalidSignatureError:
            pass
    return {}


def defaults_for_user(token: dict) -> dict:
    return getattr(settings, 'ALLOWEDFLARE_DEFAULTS_FOR_USER', lambda token: {'is_staff': True})(
        token
    )


class Allowedflare(ModelBackend):
    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> User | None:
        if not request or 'CF_Authorization' not in request.COOKIES:
            logger.warning('CF_Authorization cookie missing')
            return None
        token = decode_token(request.COOKIES['CF_Authorization'])
        if not token:
            logger.warning(f'Invalid CF_Authorization cookie {request.COOKIES["CF_Authorization"]}')
            return None
        if 'email' not in token:
            logger.warning(f'Valid token missing email {token}')

        user, new = User.objects.update_or_create(
            username=clean_username(token['email']),
            email=token['email'],
            defaults=defaults_for_user(token),
        )

        if new:
            logger.info(f'New user {user.email} authenticated with Allowedflare')
        else:
            logger.info(f'Existing user {user.email} authenticated with Allowedflare')
        return user

    def get_user(self, user_id: int) -> User | None:
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
