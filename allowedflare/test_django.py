from django.test import RequestFactory

from allowedflare import LoginView


def test_allowedflare_login_view(monkeypatch, rf: RequestFactory):
    monkeypatch.setenv('ALLOWEDFLARE_ACCESS_URL', 'off')
    response = LoginView.as_view()(rf.get(''))
    assert response.status_code == 200
    assert 'allowedflare_message' in response.context_data  # type: ignore[attr-defined]
