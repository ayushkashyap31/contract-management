"""
HTTP client for communicating with the Documenso API.
"""

from typing import Any
from urllib.parse import urljoin
from json import JSONDecodeError

import requests

from docusign_integration.config import get_settings
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
                "Content-Type": "application/json",
            }
        )

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


        if not response.content:
            return None

        try:
            return response.json()
        except ValueError as exc:
            raise DocumensoApiError(
                "Invalid JSON response received from the Documenso API."
            ) from exc

    def get(self, endpoint: str, **kwargs) -> dict[str, Any] | list[Any] | None:
        """Send a GET request."""
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> dict[str, Any] | list[Any] | None:
        """Send a POST request."""
        return self.request("POST", endpoint, **kwargs)

    def patch(self, endpoint: str, **kwargs) -> dict[str, Any] | list[Any] | None:
        """Send a PATCH request."""
        return self.request("PATCH", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> dict[str, Any] | list[Any] | None:
        """Send a DELETE request."""
        return self.request("DELETE", endpoint, **kwargs)