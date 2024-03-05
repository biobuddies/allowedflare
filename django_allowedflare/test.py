from sys import modules

from django.test import SimpleTestCase

from django_allowedflare import clean_username


class Test(SimpleTestCase):
    def test_clean_username(self):
        with self.settings(
            ALLOWEDFLARE_EMAIL_DOMAIN='off', ALLOWEDFLARE_PRIVATE_DOMAIN='domain.com'
        ):
            self.assertEqual(clean_username('user@domain.com'), 'user@domain.com')
        with self.settings(
            ALLOWEDFLARE_EMAIL_DOMAIN='domain.com', ALLOWEDFLARE_PRIVATE_DOMAIN='domain.dev'
        ):
            self.assertEqual(clean_username('user@domain.com'), 'user')
        with self.settings(ALLOWEDFLARE_PRIVATE_DOMAIN='domain.com'):
            self.assertEqual(clean_username('user@domain.com'), 'user')

    def test_fetch_or_reuse_keys(self):
        # Arrange: probably not parallel safe
        try:
            del modules['django_allowedflare']
        except KeyError:
            pass
        import django_allowedflare

        # Assert: initial conditions
        self.assertEqual(django_allowedflare.cached_keys, [])
        self.assertEqual(django_allowedflare.cache_updated.timestamp(), 0)
        with self.settings(ALLOWEDFLARE_ACCESS_URL='https://domain.cloudflareaccess.com'):
            # Act: TODO mock
            keys = django_allowedflare.fetch_or_reuse_keys()

        # Assert: module level variables are updated
        self.assertEqual(django_allowedflare.cached_keys, keys)
        self.assertGreater(django_allowedflare.cache_updated.timestamp(), 0)

        # Arrange: cleanup
        del modules['django_allowedflare']
