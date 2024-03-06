import logging
from datetime import datetime, timedelta
from datetime import timezone as datetime_timezone
from typing import Any

import requests
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse
from django.utils import timezone as django_utils_timezone
from rest_framework.authentication import BaseAuthentication
from jwt import DecodeError, InvalidSignatureError, decode
from jwt.algorithms import RSAAlgorithm

cache_updated = datetime.fromtimestamp(0, tz=datetime_timezone.utc)
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
    suffix = getattr(settings, 'ALLOWEDFLARE_EMAIL_DOMAIN', settings.ALLOWEDFLARE_PRIVATE_DOMAIN)
    return username.removesuffix(f'@{suffix}')


def configure_user(user: User, request: HttpRequest, created: bool) -> User:
    """
    Ensure the user can view all models through the admin site.

    To match `RemoteUserBackend.configure_user()`, `request` and `created` arguments are accepted
    but unused. The `self` argument is omitted to make user-provided replacement easier.
    """
    user.is_staff = True
    everyone, _ = Group.objects.get_or_create(name='allowedflare_everyone')
    everyone.permissions.add(*Permission.objects.filter(codename__startswith='view'))
    user.groups.add(everyone)
    return user


def fetch_or_reuse_keys() -> list[RSAPublicKey]:
    global cache_updated, cached_keys  # noqa: PLW0603
    now = django_utils_timezone.now()
    # As of June 2023, signing keys are documented as rotated every 6 weeks
    if cache_updated + timedelta(days=1) < now:
        response = requests.get(
            f'{settings.ALLOWEDFLARE_ACCESS_URL}/cdn-cgi/access/certs', timeout=3
        ).json()
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
    for key in fetch_or_reuse_keys():
        try:
            return decode(
                cf_authorization,
                key=key,
                audience=settings.ALLOWEDFLARE_AUDIENCE,
                algorithms=['RS256'],
            )
        except (DecodeError, InvalidSignatureError):
            pass
    return {}


def authenticate(request: HttpRequest) -> tuple[str, str, dict]:
    """
    Return a tuple with suffix-trimmed username, failure/success message, and decoded token.

    On failure to authenticate, the username will be the empty string `''` and the token will be the
    empty dictionary `{}`.
    """
    if settings.ALLOWEDFLARE_ACCESS_URL == 'off':
        return ('', 'Allowedflare is off', {})

    if 'CF_Authorization' not in request.COOKIES:
        return ('', 'Allowedflare could not find CF_Authorization cookie', {})
    cookie = request.COOKIES['CF_Authorization']
    token = decode_token(cookie)
    if not token:
        return ('', f'Allowedflare found invalid CF_Authorization cookie {cookie}', {})
    if 'email' not in token:
        return ('', f'Allowedflare could not find email within otherwise valid token {token}', {})

    cleaned_username = clean_username(token['email'])
    status = 'existing' if User.objects.filter(username=cleaned_username).exists() else 'new'
    return (cleaned_username, f'Allowedflare authenticated {status} user {cleaned_username}', token)


def update_or_create_user(username: str, request: HttpRequest, token: dict) -> User:
    user, created = User.objects.update_or_create(
        username=username, defaults={'email': token['email']}
    )
    getattr(settings, 'ALLOWEDFLARE_CONFIGURE_USER', configure_user)(user, request, created)
    return user


class Allowedflare(ModelBackend):
    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> User | None:
        if not request:
            return None
        username_from_token, message, token = authenticate(request)
        if not username_from_token:
            logger.info(message)
            return None
        # Require an explicit username so that someone with a valid token can still log in to other
        # accounts using ModelBackend or other authentication backends.
        if username != username_from_token:
            logger.info(
                f'Allowedflare found {username} != {username_from_token} (ignoring {message})'
            )
            return None
        logger.info(message)
        return update_or_create_user(username, request, token)

    def get_user(self, user_id: int) -> User | None:
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class AllowedflareLoginView(LoginView):
    template_name = 'login.html'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.username, message, _ = authenticate(self.request)
        self.extra_context = {'allowedflare_message': message}
        return super().get(request, *args, **kwargs)

    def get_form(self, form_class: type[AuthenticationForm] | None = None) -> AuthenticationForm:
        form = super().get_form(form_class)
        if getattr(self, 'username', False):
            form.fields['password'].initial = 'placeholder'
            form.fields['password'].widget.render_value = True
            form.fields['username'].initial = self.username
        return form


class DRFAuthentication(BaseAuthentication):
    def authenticate(self, request: HttpRequest) -> tuple[User | None, dict | None]:
        username, message, token = authenticate(request)
        logger.info(message)
        if not username:
            return (None, None)
        return (update_or_create_user(username, request, token), token)
