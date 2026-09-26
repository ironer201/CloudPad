"""Minimal Supabase REST client built on urllib (standard library only).

Why not supabase-py? It drags in httpx, postgrest-py, gotrue, storage3…
which alone can blow the 100 MB RAM budget on a Celeron machine.
Talking to Supabase's REST endpoints directly costs ~0 extra memory.
"""
import json
import urllib.error
import urllib.request


class CloudError(Exception):
    pass


class SupabaseClient:
    def __init__(self, url, anon_key, timeout=20):
        self.url = url.rstrip("/")
        self.anon_key = anon_key
        self.timeout = timeout

    # ------------------------------------------------------------- core
    def _request(self, method, path, payload=None, token=None,
                 prefer_representation=False):
        headers = {
            "Content-Type": "application/json",
            "apikey": self.anon_key,
            "User-Agent": "CloudPad/1.0",
        }
        if token:
            headers["Authorization"] = "Bearer " + token
        if prefer_representation:
            headers["Prefer"] = "return=representation"

        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(self.url + path, data=data,
                                     headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            raise CloudError(self._extract_error(e)) from None
        except urllib.error.URLError as e:
            raise CloudError("Network error: %s" % e.reason) from None
        return json.loads(body) if body else {}

    @staticmethod
    def _extract_error(e):
        raw = e.read().decode("utf-8", "replace")
        detail = raw
        try:
            d = json.loads(raw)
            detail = (d.get("msg") or d.get("message")
                      or d.get("error_description") or d.get("error") or raw)
        except ValueError:
            pass
        return "HTTP %d — %s" % (e.code, detail)

    # ------------------------------------------------------------- auth
    def sign_up(self, email, password):
        return self._request("POST", "/auth/v1/signup",
                             {"email": email, "password": password})

    def sign_in(self, email, password):
        return self._request("POST", "/auth/v1/token?grant_type=password",
                             {"email": email, "password": password})

    def refresh(self, refresh_token):
        return self._request("POST", "/auth/v1/token?grant_type=refresh_token",
                             {"refresh_token": refresh_token})

    def sign_out(self, token):
        return self._request("POST", "/auth/v1/logout", token=token)

    # -------------------------------------------------------- documents
    def upload_document(self, token, user_id, title, content):
        """Insert a new document; returns the new row's id."""
        rows = self._request(
            "POST", "/rest/v1/documents?select=id",
            {"user_id": user_id, "title": title, "content": content},
            token=token, prefer_representation=True)
        return rows[0]["id"] if rows else None

    def update_document(self, token, doc_id, title, content):
        self._request("PATCH", "/rest/v1/documents?id=eq." + doc_id,
                      {"title": title, "content": content}, token=token)

    def list_documents(self, token):
        """Newest 50 docs (titles only — keeps payloads small on slow CPUs)."""
        return self._request(
            "GET",
            "/rest/v1/documents?select=id,title,updated_at"
            "&order=updated_at.desc&limit=50",
            token=token)

    def download_document(self, token, doc_id):
        rows = self._request(
            "GET",
            "/rest/v1/documents?select=id,title,content&id=eq." + doc_id,
            token=token)
        return rows[0] if rows else None

    def delete_document(self, token, doc_id):
        self._request("DELETE", "/rest/v1/documents?id=eq." + doc_id,
                      token=token)