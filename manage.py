#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import sys

import default


def main() -> None:
    """Run administrative tasks."""
    try:
        from django.core.management import execute_from_command_line
        from django.core.management.commands.runserver import Command

        Command.default_addr = '0.0.0.0'  # noqa: S104
        Command.default_port = '8001'  # Should match docker-compose.yaml and gunicorn.conf.py
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            'available on your PYTHONPATH environment variable? Did you '
            'forget to activate a virtual environment?'
        ) from exc
    default.settings_module()
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
