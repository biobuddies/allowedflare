from django.test import RequestFactory
from pytest import mark

from allowedflare import LoginView


@mark.skip(reason="DJANGO_SETTINGS_MODULE / Apps aren't loaded yet problems")
def test_allowedflare_login_view(rf: RequestFactory, django_settings_module):
    response = LoginView.as_view()(rf.get(''))
    assert response.status_code == 200
    assert (
        response.context_data['allowedflare_message']  # type: ignore[attr-defined]
        == 'Allowedflare could not find CF_Authorization cookie'
    )
