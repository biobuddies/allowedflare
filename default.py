from functools import partial
from os import environ

settings_module = partial(environ.setdefault, 'DJANGO_SETTINGS_MODULE', 'demodj.settings')
