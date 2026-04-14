import os
from typing import Any, Iterable, Optional

import requests


class BDDAPIError(Exception):
    pass


class RemoteRow(dict):
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class RemoteCursor:
    def __init__(self, session: "RemoteDBSession"):
        self.session = session
        self._rows = []
        self._rowcount = 0
        self.lastrowid = None

    def execute(self, query: str, params: Optional[Iterable[Any]] = None):
        payload = self.session.execute(query, params=params)
        rows = payload.get("rows") or []
        self._rows = [RemoteRow(r) for r in rows]
        self._rowcount = payload.get("rowcount", 0)
        self.lastrowid = payload.get("lastrowid")
        return self

    @property
    def rowcount(self):
        return self._rowcount

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return self._rows


class RemoteDBSession:
    def __init__(self):
        self._last_cursor = None

    def cursor(self):
        self._last_cursor = RemoteCursor(self)
        return self._last_cursor

    def execute(self, query: str, params: Optional[Iterable[Any]] = None):
        return execute_sql(query, params=params)

    def commit(self):
        return None

    def close(self):
        return None


def _base_url() -> str:
    return os.getenv("BDD_API_URL", "http://127.0.0.1:5001").rstrip("/")


def _headers() -> dict[str, str]:
    token = os.getenv("BDD_SERVICE_TOKEN", "")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _handle_response(response: requests.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError:
        payload = {"error": response.text}

    if response.status_code >= 400:
        raise BDDAPIError(payload.get("error") or payload.get("erreur") or f"Erreur BDD API ({response.status_code})")
    return payload


def execute_sql(query: str, params: Optional[Iterable[Any]] = None) -> dict[str, Any]:
    response = requests.post(
        f"{_base_url()}/mbt/sql/execute",
        headers=_headers(),
        json={"query": query, "params": list(params or [])},
        timeout=10,
    )
    return _handle_response(response)


def execute_script(script: str) -> dict[str, Any]:
    response = requests.post(
        f"{_base_url()}/mbt/sql/script",
        headers=_headers(),
        json={"script": script},
        timeout=10,
    )
    return _handle_response(response)


def get_db_session() -> RemoteDBSession:
    return RemoteDBSession()
