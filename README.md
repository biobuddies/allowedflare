Authenticate to Django with JSON Web Tokens (JWTs) signed by Cloudflare Access. A Django reimplementation of https://developers.cloudflare.com/cloudflare-one/identity/authorization-cookie/validating-json/#python-example

To run the demo, export these environment variables
* `ALLOWEDFLARE_ACCESS_URL` https://your-organization.cloudflareaccess.com
* `ALLOWEDFLARE_AUDIENCE` 64-character hexidecimal string
* `ALLOWEDFLARE_PRIVATE_DOMAIN` your-domain.tld

Then run
```
docker-compose up
```

Configure Cloudflare Tunnel public hostname demodj.your-domain.tld to http://localhost:8001 or equivalent.

### TODO
* Better login page
* Django REST Framework (DRF) support
* Grant users view permission to all models
* (Re-) authenticating proxy for different-domain front-ends, like https://developers.cloudflare.com/cloudflare-one/identity/authorization-cookie/cors/#send-authentication-token-with-cloudflare-worker but
    - Setting username so it can be logged by gunicorn
    - Rewriting origin redirects
    - Setting the XmlHttpRequest(?) header to avoid redirects to the sign-in page
    - Will the original CF_Authorization cookie need to be copied, similar to X-Forwarded-For?
