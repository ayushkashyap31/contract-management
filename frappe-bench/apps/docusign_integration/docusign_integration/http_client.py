"""
HTTP client for communicating with the Documenso API.
"""

from typing import Any
from urllib.parse import urljoin
from json import JSONDecodeError

import requests

from docusign_integration.integration_config import get_settings
from docusign_integration.exceptions import (
    DocumensoApiError,
    DocumensoAuthenticationError,
    DocumensoRequestError,
)


class DocumensoHttpClient:
    """HTTP client for communicating with the Documenso API."""

    def __init__(self):
        """Initialize the HTTP client using Documenso integration settings."""
        settings = get_settings()

        self.base_url = settings.base_url
        self.timeout = settings.request_timeout

        token = settings.get_password("api_token")

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            }
        )

    def _send(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ):
        """
        Execute an HTTP request and return the raw response after mapping
        transport, authentication and API errors onto the exception hierarchy.

        Raises:
            DocumensoRequestError: If the request cannot be completed.
            DocumensoAuthenticationError: If authentication fails.
            DocumensoApiError: If the API returns an error response.
        """
        url = urljoin(self.base_url, endpoint)

        kwargs.setdefault("timeout", self.timeout)

        try:
            response = self.session.request(
                method=method,
                url=url,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise DocumensoRequestError(
                "Failed to communicate with the Documenso API."
            ) from exc

        if response.status_code in (401, 403):
            raise DocumensoAuthenticationError(
                "Authentication with the Documenso API failed."
            )

        if not response.ok:
            try:
                error = response.json()
                message = error.get("message") or error.get("error")
            except JSONDecodeError:
                message = None

            raise DocumensoApiError(
                message or f"Documenso API returned HTTP {response.status_code}."
            )

        return response

    def request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> dict[str, Any] | list[Any] | None:
        """
        Execute an HTTP request and return the parsed JSON response.

        Raises:
            DocumensoRequestError: If the request cannot be completed.
            DocumensoAuthenticationError: If authentication fails.
            DocumensoApiError: If the API returns an error or invalid JSON.
        """
        response = self._send(method, endpoint, **kwargs)

        if not response.content:
            return None

        try:
            return response.json()
        except ValueError as exc:
            raise DocumensoApiError(
                "Invalid JSON response received from the Documenso API."
            ) from exc

    def request_binary(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> bytes:
        """
        Execute an HTTP request and return the raw binary response body.

        Used for endpoints that stream files (e.g. signed PDF downloads).

        Raises:
            DocumensoRequestError: If the request cannot be completed.
            DocumensoAuthenticationError: If authentication fails.
            DocumensoApiError: If the API returns an error or an empty body.
        """
        response = self._send(method, endpoint, **kwargs)

        if not response.content:
            raise DocumensoApiError(
                "Empty response received from the Documenso API."
            )

        return response.content

    def get(self, endpoint: str, **kwargs) -> dict[str, Any] | list[Any] | None:
        """Send a GET request."""
        return self.request("GET", endpoint, **kwargs)

    def get_binary(self, endpoint: str, **kwargs) -> bytes:
        """Send a GET request and return the raw binary response body."""
        return self.request_binary("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> dict[str, Any] | list[Any] | None:
        """Send a POST request."""
        return self.request("POST", endpoint, **kwargs)

    def patch(self, endpoint: str, **kwargs) -> dict[str, Any] | list[Any] | None:
        """Send a PATCH request."""
        return self.request("PATCH", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> dict[str, Any] | list[Any] | None:
        """Send a DELETE request."""
        return self.request("DELETE", endpoint, **kwargs)