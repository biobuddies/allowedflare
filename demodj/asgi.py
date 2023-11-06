"""
ASGI config for demo project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""


from django.core.asgi import get_asgi_application

import set_default_django_settings_module  # noqa: F401

application = get_asgi_application()
