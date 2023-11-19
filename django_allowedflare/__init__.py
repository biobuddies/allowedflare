import logging
from datetime import datetime, timezone as datetime_timezone
from typing import Any, Optional

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.utils import timezone as django_utils_timezone
from django.conf import settings
from jwt.algorithms import RSAAlgorithm
from jwt import decode, InvalidSignatureError
import requests


logger = logging.getLogger(__name__)


def defaults_for_user(decoded_token: str) -> dict:
    # TODO put this in settings
    return {'is_staff': True}


cache_updated = datetime.fromtimestamp(0, tz=datetime_timezone.utc)
cached_keys: list[RSAPublicKey] = []


def fetch_or_reuse_keys():
    global cache_updated, cached_keys
    now = django_utils_timezone.now()
    # As of June 2023, signing keys are documented as rotated every 6 weeks
    if cache_updated + django_utils_timezone.timedelta(days=1) < now:
        response = requests.get(f'{settings.ALLOWEDFLARE_ACCESS_URL}/cdn-cgi/access/certs').json()
        if response.get('keys'):
            cached_keys = [RSAAlgorithm.from_jwk(key) for key in response['keys']]
            cache_updated = now
    return cached_keys


def decode_token(cf_authorization: str):
    for key in fetch_or_reuse_keys():
        try:
            return decode(cf_authorization, key=key, audience=settings.ALLOWEDFLARE_AUDIENCE, algorithms=['RS256'])
        except InvalidSignatureError:
            pass
    return None


class Allowedflare(BaseBackend):
    def authenticate(self, request: Optional[HttpRequest], **kwargs: Any) -> Optional[AbstractBaseUser]:
        if not request or 'CF_Authorization' not in request.COOKIES:
            return None
        token = decode_token(request.COOKIES['CF_Authorization'])
        if not token:
            return None

        user, new = User.objects.update_or_create(email=token['email'], defaults=defaults_for_user(token))
        if new:
            logger.info(f'New user {user.email} authenticated using Allowedflare')
        else:
            logger.debug(f'Existing user {user.email} authenticated using Allowedflare')
        return user
