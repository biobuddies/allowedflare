from jwt import encode
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from allowedflare import authenticate, clean_username


def test_clean_username_unmodified(monkeypatch):
    monkeypatch.delenv('ALLOWEDFLARE_EMAIL_DOMAIN', raising=False)
    monkeypatch.delenv('ALLOWEDFLARE_PRIVATE_DOMAIN', raising=False)
    assert clean_username('user@domain.com') == 'user@domain.com'

    monkeypatch.setenv('ALLOWEDFLARE_EMAIL_DOMAIN', 'off')
    monkeypatch.setenv('ALLOWEDFLARE_PRIVATE_DOMAIN', 'domain.com')
    assert clean_username('user@domain.com') == 'user@domain.com'


def test_clean_username_email_domain_removed(monkeypatch):
    monkeypatch.setenv('ALLOWEDFLARE_PRIVATE_DOMAIN', 'domain.dev')
    monkeypatch.setenv('ALLOWEDFLARE_EMAIL_DOMAIN', 'domain.com')
    assert clean_username('user@domain.com') == 'user'


def test_clean_username_private_domain_removed(monkeypatch):
    monkeypatch.setenv('ALLOWEDFLARE_PRIVATE_DOMAIN', 'domain.com')
    assert clean_username('user@domain.com') == 'user'


def test_authenticate_off(monkeypatch):
    monkeypatch.setenv('ALLOWEDFLARE_ACCESS_URL', 'off')
    assert authenticate({}) == ('', 'Allowedflare is off', {})


# TODO make these offline


# TODO check Cf-Access-Jwt-Assertion header as fallback, or whatever `cloudflared curl` sets
def test_authenticate_no_cookie(monkeypatch):
    monkeypatch.setenv('ALLOWEDFLARE_ACCESS_URL', 'https://demo.cloudflareaccess.com')
    assert authenticate({}) == ('', 'Allowedflare could not find CF_Authorization cookie', {})


def test_authenticate_invalid_token(monkeypatch):
    monkeypatch.setenv('ALLOWEDFLARE_ACCESS_URL', 'https://demo.cloudflareaccess.com')
    user, message, token = authenticate({'CF_Authorization': 'invalid'})
    assert user == ''
    assert message.startswith('Allowedflare failed to decode CF_Authorization cookie invalid')
    assert token == {}


def test_authenticate_jwk_client_error(monkeypatch):
    monkeypatch.setenv('ALLOWEDFLARE_ACCESS_URL', 'https://demo.cloudflareaccess.com')
    user, message, token = authenticate(
        {
            'CF_Authorization': 'eyJhbGciOiJSUzI1NiIsImtpZCI6ImQ3MmNiNTgzMTZjMTc5NjdhYmY1OTlkNWFkNWJiZjkwYzM2NDk4N2UxNWYxNTdhMWZkNjljZmNiODg0Y2I3ZTYifQ.eyJhdWQiOlsiMDhmY2UyMTA5M2E0OGIwMTAwNTBjZTUwZmVmYTYxYjNkN2Q2YTA1NDAzNWY3NzlkM2M1OTM0ZTVlOTE4NTYwNyJdLCJlbWFpbCI6ImNvdkBteWtvbGFiLmNvbSIsImFjY291bnRfaWQiOiJjYTVjYmMwNDc5M2IwM2RhM2QxZGJjY2VmODQ0ZWFkMCIsImV4cCI6MTcxNDczNzIyOCwiaWF0IjoxNzE0NjUwODI4LCJuYmYiOjE3MTQ2NTA4MjgsImlzcyI6Imh0dHBzOi8vY292cmFjZXIuY2xvdWRmbGFyZWFjY2Vzcy5jb20iLCJzdWIiOiI3M2ViN2UxZC01MDllLTU5MWItODA5Ni03ZjVjY2MyNDE3ODUiLCJpZGVudGl0eSI6eyJlbWFpbCI6ImNvdkBteWtvbGFiLmNvbSIsImlkcCI6eyJpZCI6ImU5MGIzNWFjLTdhYzQtNGJhYy1hNDkxLTA0ZjUzZjIwYjA3NSIsInR5cGUiOiJvbmV0aW1lcGluIn0sImdlbyI6eyJjb3VudHJ5IjoiVVMifSwidXNlcl91dWlkIjoiNzNlYjdlMWQtNTA5ZS01OTFiLTgwOTYtN2Y1Y2NjMjQxNzg1IiwiYWNjb3VudF9pZCI6ImNhNWNiYzA0NzkzYjAzZGEzZDFkYmNjZWY4NDRlYWQwIiwiaWF0IjoxNzE0NjUwODI4LCJpcCI6IjEzNi41NC4zMy40OCIsImF1dGhfc3RhdHVzIjoiTk9ORSIsImNvbW1vbl9uYW1lIjoiIiwic2VydmljZV90b2tlbl9pZCI6IiIsInNlcnZpY2VfdG9rZW5fc3RhdHVzIjpmYWxzZSwiaXNfd2FycCI6ZmFsc2UsImlzX2dhdGV3YXkiOmZhbHNlLCJkZXZpY2VfaWQiOiIiLCJtdGxzX2F1dGgiOnsiY2VydF9pc3N1ZXJfZG4iOiIiLCJjZXJ0X3NlcmlhbCI6IiIsImNlcnRfaXNzdWVyX3NraSI6IiIsImNlcnRfcHJlc2VudGVkIjp0cnVlLCJjb21tb25fbmFtZSI6IiIsImF1dGhfc3RhdHVzIjoiTk9ORSJ9LCJ2ZXJzaW9uIjoyfSwidHlwZSI6Im9yZyIsImlkZW50aXR5X25vbmNlIjoiQkp0RGtxRk1xb0pkQ0lJeSJ9.oNzosGw5BVfv99DWyO-8hZ3cGncd7gv85twoGgK8YJ41RG8AKlb2pXtFZlgqnD6cVHXuCONdxLpuB56Y-aSy2uG_ELcMmoirovHn6nsH7OUweh-aAb9FC90MCzmxl7soKgeobd4f6XgYwZeqmez8nuich58vIBgAcNbs9aBQMRoGV7y5ac57Fram1goAALLH_AZIxE-ajMXEdbw4Jt6DEYEGvon54UFeOAsTO7IGNySdVhH0oTg6pirHt40YlcwNMD77z54Epx76Tl5TcLH1OxuROnFpSR49g5mIcxq9lEJ6W26-JtLC51BJbVM4Lw-_Y478uKBYUvEMjiETCDog-Q'
        }
    )
    assert user == ''
    assert 'Unable to find a signing key that matches' in message
    assert token == {}


def test_authenticate_valid_signature(monkeypatch):
    private_key = generate_private_key(65537, 512, default_backend())
    print(
        private_key.sign(
            b'payload',
            padding.PSS(mgf=padding.MGF1(SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            SHA256(),
        )
    )
    cookies = {'CF_Authorization': encode({}, 'secret')}
    user, message, token = authenticate(cookies)
