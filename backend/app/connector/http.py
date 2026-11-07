"""Blocking GraphDB HTTP transport, run from worker threads by the async clients."""

import base64
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class GraphDBError(RuntimeError):
    """Base class for transport failures."""


class GraphDBTimeout(GraphDBError):
    """The request did not finish before its deadline."""


class GraphDBUnavailable(GraphDBError):
    """GraphDB could not be reached."""


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status: int
    body: str


class GraphDBHttp:
    """Small HTTP client with no retries and an explicit deadline per request."""

    def __init__(self, host: str, user: str, password: str) -> None:
        self.base_url = host.rstrip("/")
        credentials = base64.b64encode(f"{user}:{password}".encode()).decode()
        self.auth_header = f"Basic {credentials}"

    def request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        deadline: float | None = None,
        accept: str = "application/json",
    ) -> HttpResponse:
        timeout = self._remaining(deadline)
        headers = {"Authorization": self.auth_header, "Accept": accept}
        data: bytes | None = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload, ensure_ascii=False).encode()
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            method=method,
            headers=headers,
            data=data,
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return HttpResponse(response.status, response.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as error:
            return HttpResponse(error.code, error.read().decode("utf-8", "replace"))
        except TimeoutError as error:
            raise GraphDBTimeout("GraphDB request timed out") from error
        except urllib.error.URLError as error:
            if isinstance(error.reason, TimeoutError):
                raise GraphDBTimeout("GraphDB request timed out") from error
            raise GraphDBUnavailable("GraphDB is unreachable") from error

    def options(self, path: str, deadline: float | None = None) -> HttpResponse:
        return self.request("OPTIONS", path, deadline=deadline, accept="*/*")

    @staticmethod
    def _remaining(deadline: float | None) -> float | None:
        if deadline is None:
            return None
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise GraphDBTimeout("GraphDB request deadline exceeded")
        return remaining
