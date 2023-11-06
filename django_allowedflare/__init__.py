import logging
from datetime import timezone as datetime_timezone
from typing import Any, Optional

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

logger.info('covdebug')


def defaults_for_user(decoded_token: str) -> dict:
    # TODO put this in settings
    return {'is_staff': True}


cache_updated = django_utils_timezone.datetime.fromtimestamp(0, tz=datetime_timezone.utc)
cached_keys: list[str] = []


def fetch_or_reuse_keys():
    global cache_updated, cached_keys
    # As of June 2023, signing keys are documented as rotated every 6 weeks
    if cache_updated + django_utils_timezone.timedelta(days=1) < django_utils_timezone.now():
        response = requests.get(f'{settings.CLOUDFLARE_ACCESS_URL}/cdn-cgi/access/certs').json()
        if response.get('keys'):
            cached_keys = response['keys']
            cache_updated = django_utils_timezone.now()
    return cached_keys


def decode_token(cf_authorization: HttpRequest):
    for key in fetch_or_reuse_keys():
        try:
            return decode(
                cf_authorization,
                key=RSAAlgorithm.from_jwk(key),
                audience=settings.CLOUDLARE_ACCESS_AUD,
                algorithms=['RS256'],
            )
        except InvalidSignatureError:
            pass
    return None


class Allowedflare(BaseBackend):
    def authenticate(self, request: Optional[HttpRequest], **kwargs: Any) -> Optional[AbstractBaseUser]:
        logger.error(f'covdebug {request.COOKIES}')
        if not request or 'CF_Authorization' not in request.COOKIES:
            return None
        token = decode_token(request.COOKIES['CF_Authorization'])
        if not token:
            return None

        return User.objects.update_or_create(email=token['email'], defaults=defaults_for_user(token))[0]
