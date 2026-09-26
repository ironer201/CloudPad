"""In-memory session. Authentication is ONLY required for cloud features —
the app works fully offline until the user touches a cloud button."""


class AuthState:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        self.user_email = None

    @property
    def logged_in(self):
        return self.access_token is not None

    def set_session(self, session):
        self.access_token = session.get("access_token")
        self.refresh_token = session.get("refresh_token")
        user = session.get("user") or {}
        self.user_id = user.get("id")
        self.user_email = user.get("email")

    def clear(self):
        self.__init__()