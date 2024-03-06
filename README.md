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
* Unit tests
* Example configuration using Helicopyter
* End-to-end tests

## Open Questions
* Do existing projects like
  https://django-rest-framework-simplejwt.readthedocs.io/en/latest/index.html
  already provide this functionality?
* Should Allowedflare provide a subclass of
  [RemoteUserMiddleware](https://docs.djangoproject.com/en/5.0/howto/auth-remote-user/)
  to automatically login each request?
* Are there Free/Libre/Open Source alternatives to Cloudflare Access and Okta that I can run
  end-to-end tests against?
