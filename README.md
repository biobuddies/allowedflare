Authenticate to Django with JSON Web Tokens (JWTs) signed by Cloudflare Access. A Django reimplementation of https://developers.cloudflare.com/cloudflare-one/identity/authorization-cookie/validating-json/#python-example

To run the demo, set the following environment variables:
```
export ALLOWEDFLARE_ACCESS_URL=https://your-organization.cloudflareaccess.com
export ALLOWEDFLARE_AUDIENCE=64-character hexadecimal string
export ALLOWEDFLARE_PRIVATE_DOMAIN=your-domain.tld
```

Then run
```
docker compose up
```

Configure Cloudflare Tunnel public hostname demodj.your-domain.tld to http://localhost:8001 or equivalent.

## Customizing user setup

On every authenticated request, the backend calls `configure_user(user, request, created)`,
which by default makes the user staff and grants all `view_*` permissions to an
`allowedflare_everyone` group so everyone can browse the admin site read-only. Set
`ALLOWEDFLARE_CONFIGURE_USER` in settings to replace it.

The default re-checks group permissions on every request (a few queries). If you'd rather pay
nothing on the request path, do per-user setup only on creation and sync group permissions at
`post_migrate` — the only moment new permissions can come into existence:

```python
# settings.py
def ALLOWEDFLARE_CONFIGURE_USER(user, request, created):
    from yourapp.allowedflare_user import configure_user
    return configure_user(user, request, created)

# yourapp/allowedflare_user.py
from django.contrib.auth.models import Group, Permission

def configure_user(user, request, created):
    if created:
        user.is_staff = True
        user.save()
        everyone, _ = Group.objects.get_or_create(name='allowedflare_everyone')
        user.groups.add(everyone)
    return user

def sync_everyone_permissions(sender, **kwargs):
    everyone, _ = Group.objects.get_or_create(name='allowedflare_everyone')
    missing = Permission.objects.filter(codename__startswith='view').exclude(group=everyone)
    if missing.exists():
        everyone.permissions.add(*missing)

# yourapp/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate

class YourAppConfig(AppConfig):
    name = 'yourapp'

    def ready(self):
        from yourapp.allowedflare_user import sync_everyone_permissions
        post_migrate.connect(sync_everyone_permissions, weak=False)
```

### TODO
* Iterate on the same-origin (re-)authenticating proxy
    - From-scratch reimplementation of https://developers.cloudflare.com/cloudflare-one/identity/authorization-cookie/cors/#send-authentication-token-with-cloudflare-worker
    - Setting username so it can be logged by gunicorn
    - Setting the XmlHttpRequest(?) header to avoid redirects to the sign-in page
* Iterate on Admin site ModelBackend
    - http://localhost:8001/admin/login/ text when authenticated is "You are authenticated as , but are not authorized to access this page. Would you like to login to a different account?"
* Expand unit test coverage
* Basic integration and end-to-end tests
* mTLS support and testing
* Configure PostgreSQL
    - Post-migration hook to create a `readonly` DB user
    - Use the `readonly` DB user for django-sql-explorer and jupyterhub
    - Update the django-sql-explorer allowlist to accept `SET` since it's only dangerous for MySQL
    - Exclude only specific fields, like password hash, from the django-sql-explorer view of the django.contrib.auth schema
    - See if admin site change history fields can be shown in the django-sql-explorer schema viewer

## Open Questions
* Do existing projects like django-allauth or
  https://django-rest-framework-simplejwt.readthedocs.io/en/latest/index.html
  already provide this functionality?
* What about [RemoteUserMiddleware](https://docs.djangoproject.com/en/5.0/howto/auth-remote-user/)?
* Should this package help with [Wide Key `=` Equals Value Logging](https://cov.ing/ton/blog/2026/02/22/wini-wide-key-equals-value-logging/) now that it is already starting to customize Gunicorn?
* Are there Free/Libre/Open Source alternatives to Cloudflare Access and Okta that I can run
  end-to-end tests against?
