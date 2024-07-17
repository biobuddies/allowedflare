from django.test import RequestFactory

from allowedflare import LoginView


def test_allowedflare_login_view(rf: RequestFactory):
    response = LoginView.as_view()(rf.get(''))
    assert response.status_code == 200
    assert (
        response.context_data['allowedflare_message']  # type: ignore[attr-defined]
        == 'Allowedflare could not find CF_Authorization cookie'
    )
