from datetime import timedelta
from typing import Any

from gunicorn.config import Config

class Logger:
    def __init__(self, cfg: Config) -> None: ...
    def atoms(
        self, resp: Any, req: Any, environ: dict[str, Any], request_time: timedelta
    ) -> dict[str, Any]: ...
    def _get_user(self, environ: dict[str, Any]) -> str: ...
