from pytest import fixture

from default import settings_module


@fixture(autouse=True)
def django_settings_module(monkeypatch):
    print(*settings_module.args)
    monkeypatch.setenv(*settings_module.args)
