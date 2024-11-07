# To avoid "AppRegistryNotReady: Apps aren't loaded yet." and similar problems, this file must
# only import from the likes of allowedflare.core, not the likes of allowedflare.django.

from allowedflare.core import authenticate, clean_username

__all__ = (authenticate.__name__, clean_username.__name__)
