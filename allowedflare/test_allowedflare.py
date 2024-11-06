from jwt import encode
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from cryptography.hazmat.backends import default_backend
from datetime import UTC, datetime

from allowedflare import clean_username
from allowedflare.allowedflare import authenticate


def test_clean_username_unmodified(monkeypatch):
    monkeypatch.delenv('ALLOWEDFLARE_EMAIL_REGEX', raising=False)
    monkeypatch.delenv('ALLOWEDFLARE_PRIVATE_DOMAIN', raising=False)
    assert clean_username('user@domain.com') == 'user@domain.com'

    monkeypatch.setenv('ALLOWEDFLARE_EMAIL_REGEX', 'off')
    monkeypatch.setenv('ALLOWEDFLARE_PRIVATE_DOMAIN', 'domain.com')
    assert clean_username('user@domain.com') == 'user@domain.com'


def test_clean_username_email_domain_removed(monkeypatch):
    monkeypatch.setenv('ALLOWEDFLARE_EMAIL_REGEX', 'domain\.com')
    assert clean_username('user@domain.com') == 'user'


def test_clean_username_regex(monkeypatch):
    monkeypatch.setenv('ALLOWEDFLARE_EMAIL_REGEX', r'(domain\.com|domain\.org)')
    assert clean_username('first.user@domain.com') == 'first.user'
    assert clean_username('second.user@domain.net') == 'second.user@domain.net'
    assert clean_username('third.user@domain.org') == 'third.user'


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
    private_key = generate_private_key(65537, 512, default_backend())
    monkeypatch.setenv('ALLOWEDFLARE_ACCESS_URL', 'https://demo.cloudflareaccess.com')
    user, message, token = authenticate({'CF_Authorization': encode({}, private_key, 'RS256')})
    assert user == ''
    assert 'Unable to find a signing key that matches' in message
    assert token == {}


def test_authenticate_valid_token(mocker, monkeypatch):
    private_key = generate_private_key(65537, 512, default_backend())
    token = {
        'aud': 'audience',
        'email': 'firstname.lastname@domain.com',
        'exp': int(datetime.now(UTC).timestamp() + 100),
    }
    cookies = {'CF_Authorization': encode(token, private_key, 'RS256')}
    monkeypatch.setenv('ALLOWEDFLARE_ACCESS_URL', 'https://demo.cloudflareaccess.com')
    monkeypatch.setenv('ALLOWEDFLARE_AUDIENCE', 'audience')
    mock_get_signing_key_from_jwt = mocker.patch(
        'allowedflare.allowedflare.PyJWKClient.get_signing_key_from_jwt', autospec=True
    )
    mock_get_signing_key_from_jwt.return_value.key = private_key.public_key()

    assert authenticate(cookies) == (
        'firstname.lastname@domain.com',
        'Allowedflare authenticated firstname.lastname@domain.com',
        token,
    )
