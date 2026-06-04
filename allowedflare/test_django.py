import pytest
from django.contrib.auth.models import Group, Permission, User
from django.db import connection
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext

from allowedflare.django import LoginView, configure_user


def test_allowedflare_login_view(monkeypatch, rf: RequestFactory):
    monkeypatch.setenv('ALLOWEDFLARE_ACCESS_URL', 'off')
    response = LoginView.as_view()(rf.get(''))
    assert response.status_code == 200
    assert 'allowedflare_message' in response.context_data  # type: ignore[attr-defined]


@pytest.mark.django_db
def test_configure_user_attempts_no_inserts_in_steady_state(rf: RequestFactory):
    """Repeat calls must not attempt conflicting inserts.

    On PostgreSQL, M2M add() of already-present rows runs INSERT ... ON CONFLICT DO NOTHING,
    which consumes a sequence value per attempted row even though nothing is inserted. At one
    call per authenticated request, this eventually overflows the int4
    auth_group_permissions.id.
    """
    user = User.objects.create(username='sailor')
    configure_user(user, rf.get(''), True)

    user.refresh_from_db()
    assert user.is_staff
    assert user.groups.filter(name='allowedflare_everyone').exists()
    everyone = Group.objects.get(name='allowedflare_everyone')
    assert everyone.permissions.filter(codename__startswith='view').count() == (
        Permission.objects.filter(codename__startswith='view').count()
    )

    with CaptureQueriesContext(connection) as context:
        configure_user(user, rf.get(''), False)

    inserts = [
        q['sql'] for q in context.captured_queries if q['sql'].lstrip().upper().startswith('INSERT')
    ]
    assert inserts == []
