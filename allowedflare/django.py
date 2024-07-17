import logging
from typing import Any

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.http import HttpRequest, HttpResponse

# Can be shortened to django.http.HttpResponseBase in 4.1 and newer
# https://github.com/django/django/pull/15667/commits/7e003fa06a40c72f7f442876e1eb2611115df80c
from django.http.response import HttpResponseBase
from rest_framework.authentication import BaseAuthentication

from allowedflare.allowedflare import authenticate

logger = logging.getLogger(__name__)


def configure_user(user: User, request: HttpRequest, created: bool) -> User:
    """
    Ensure the user can view all models through the admin site.

    To match `RemoteUserBackend.configure_user()`, `request` and `created` arguments are accepted
    but unused. The `self` argument is omitted to make user-provided replacement easier.
    """
    user.is_staff = True
    user.save()

    everyone, _ = Group.objects.get_or_create(name='allowedflare_everyone')
    everyone.permissions.add(*Permission.objects.filter(codename__startswith='view'))
    user.groups.add(everyone)
    return user


def update_or_create_user(username: str, request: HttpRequest, token: dict) -> User:
    if 'email' in token:
        defaults = {'email': token['email']}
    else:
        defaults = {}
    user, created = User.objects.update_or_create(username=username, defaults=defaults)
    getattr(settings, 'ALLOWEDFLARE_CONFIGURE_USER', configure_user)(user, request, created)
    return user


class Backend(ModelBackend):
    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> User | None:
        if not request:
            return None
        username_from_token, message, token = authenticate(request.COOKIES)
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


class LoginView(DjangoLoginView):
    template_name = 'login.html'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.username, message, _ = authenticate(self.request.COOKIES)
        self.extra_context = {**(self.extra_context or {}), 'allowedflare_message': message}
        return super().get(request, *args, **kwargs)

    def get_form(self, form_class: type[AuthenticationForm] | None = None) -> AuthenticationForm:
        form = super().get_form(form_class)
        if getattr(self, 'username', False):
            form.fields['password'].initial = 'placeholder'
            form.fields['password'].widget.render_value = True
            form.fields['username'].initial = self.username
        return form


def login_view_wrapper(request: HttpRequest) -> HttpResponseBase:
    return LoginView.as_view(
        extra_context={'title': 'Log In', REDIRECT_FIELD_NAME: request.get_full_path()}
    )(request)


class Authentication(BaseAuthentication):
    def authenticate(self, request: HttpRequest) -> tuple[User | None, dict | None]:
        username, message, token = authenticate(request.COOKIES)
        logger.info(message)
        if not username:
            return (None, None)
        return (update_or_create_user(username, request, token), token)
