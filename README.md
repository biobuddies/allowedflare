Authenticate to Django with JSON Web Tokens (JWTs) signed by Cloudflare Access. A Django reimplementation of https://developers.cloudflare.com/cloudflare-one/identity/authorization-cookie/validating-json/#python-example

To run the demo, set the following environment variables:
```
export ALLOWEDFLARE_ACCESS_URL=https://your-organization.cloudflareaccess.com
export ALLOWEDFLARE_AUDIENCE=64-character hexidecimal string
export ALLOWEDFLARE_PRIVATE_DOMAIN=your-domain.tld
```

Then run
```
docker compose up
```

Configure Cloudflare Tunnel public hostname demodj.your-domain.tld to http://localhost:8001 or equivalent.

### TODO
* Same-origin (re-)authenticating proxy
    - Like https://developers.cloudflare.com/cloudflare-one/identity/authorization-cookie/cors/#send-authentication-token-with-cloudflare-worker
    - Setting username so it can be logged by gunicorn
    - Rewriting origin redirects
    - Setting the XmlHttpRequest(?) header to avoid redirects to the sign-in page
    - Will the original CF_Authorization cookie need to be copied, similar to X-Forwarded-For?
* Admin site ModelBackend
    - http://localhost:8001/admin/login/ text when authenticated is "You are authenticated as , but are not authorized to access this page. Would you like to login to a different account?"
* Unit tests
* Example configuration using Helicopyter
* End-to-end tests
* mTLS support and testing
* Configure PostgreSQL
    - Post-migration hook to create a `readonly` DB user
    - Use the `readonly` DB user for django-sql-explorer and jupyterhub
    - Update the django-sql-explorer allowlist to accept `SET` since it's only dangerous for MySQL
    - Exclude only specific fields, like password hash, from the django-sql-explorer view of the django.contrib.auth schema
    - See if admin site change history fields can be shown in the django-sql-explorer schema viewer

## Open Questions
* Do existing projects like
  https://django-rest-framework-simplejwt.readthedocs.io/en/latest/index.html
  already provide this functionality?
* Should Allowedflare provide a subclass of
  [RemoteUserMiddleware](https://docs.djangoproject.com/en/5.0/howto/auth-remote-user/)
  to automatically login each request?
* Are there Free/Libre/Open Source alternatives to Cloudflare Access and Okta that I can run
  end-to-end tests against?
