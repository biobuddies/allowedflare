from jupyterhub.auth import Authenticator  # type: ignore
from tornado.web import RequestHandler

from allowedflare.allowedflare import authenticate


class JupyterHub(Authenticator):
    auto_login = True

    # New configurable trait

    async def get_authenticated_user(self, handler: RequestHandler, data):
        username, message, token = authenticate(handler.request.cookies)
        self.log.info(message)
        if not username:
            return None
        return {
            'name': username,
            'admin': True,  # TODO look at groups or something
        }
