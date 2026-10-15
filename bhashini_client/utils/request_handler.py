import json
from typing import Optional

import requests

from ..config import API_KEY, BASE_URL, DEFAULT_HEADERS, DEFAULT_TIMEOUT


class RequestHandler:
    def __init__(self, api_key: Optional[str] = None):
        auth_token = (api_key or API_KEY).strip()
        self.api_key = auth_token
        self.headers = {**DEFAULT_HEADERS, "Authorization": auth_token}

    def post(self, payload: dict, url: Optional[str] = None, headers: Optional[dict] = None):
        try:
            request_headers = {**self.headers, **(headers or {})}
            response = requests.post(
                url or BASE_URL,
                headers=request_headers,
                data=json.dumps(payload),
                timeout=DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return None
