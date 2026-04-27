import os
from typing import Any, Iterable

import requests
from dotenv import load_dotenv

load_dotenv()

BDD_API_URL = os.getenv("BDD_API_URL", "http://127.0.0.1:5001")
BDD_SERVICE_TOKEN = os.getenv("BDD_SERVICE_TOKEN")


class BDDAPIError(Exception):
    pass


def _headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if BDD_SERVICE_TOKEN:
        headers["Authorization"] = f"Bearer {BDD_SERVICE_TOKEN}"
    return headers


def _handle_response(response: requests.Response) -> Any:
    try:
        payload = response.json()
    except Exception:
        payload = response.text

    if response.status_code >= 400:
        raise BDDAPIError(f"{response.status_code} - {payload}")
    return payload


def get_json(path: str):
    url = f"{BDD_API_URL}{path}"
    response = requests.get(url, headers=_headers(), timeout=120)
    return _handle_response(response)


def post_json(path: str, data: Any):
    url = f"{BDD_API_URL}{path}"
    response = requests.post(url, json=data, headers=_headers(), timeout=120)
    return _handle_response(response)


def patch_json(path: str, data: Any):
    url = f"{BDD_API_URL}{path}"
    response = requests.patch(url, json=data, headers=_headers(), timeout=120)
    return _handle_response(response)


def delete_json(path: str):
    url = f"{BDD_API_URL}{path}"
    response = requests.delete(url, headers=_headers(), timeout=120)
    return _handle_response(response)


def execute_sql(query: str, params: Iterable[Any] | None = None):
    return post_json('/mbt/sql/execute', {
        'query': query,
        'params': list(params or []),
    })


def execute_script(script: str):
    return post_json('/mbt/sql/script', {'script': script})


class RemoteCursor:
    def __init__(self):
        self._rows = []
        self.lastrowid = None
        self.rowcount = 0

    def execute(self, query: str, params: Iterable[Any] | None = None):
        payload = execute_sql(query, params or [])
        self._rows = payload.get('rows', [])
        self.lastrowid = payload.get('lastrowid')
        self.rowcount = payload.get('rowcount', 0)
        return self

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class RemoteDBSession(RemoteCursor):
    def cursor(self):
        return self

    def commit(self):
        return None

    def close(self):
        return None


def get_db_session():
    return RemoteDBSession()
