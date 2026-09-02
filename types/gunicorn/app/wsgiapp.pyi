from typing import Any

class WSGIApplication:
    cfg: Any

    def __init__(self, usage: str | None = None, prog: str | None = None) -> None: ...
    def load_config_from_file(self, filename: str) -> None: ...
