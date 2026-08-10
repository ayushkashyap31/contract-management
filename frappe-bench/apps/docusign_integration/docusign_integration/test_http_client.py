# Copyright (c) 2026, Ayush Kumar Kashyap and contributors
# For license information, please see license.txt

"""Tests for the Documenso HTTP client, focusing on binary downloads."""

from json import JSONDecodeError
from types import SimpleNamespace
from unittest.mock import Mock, patch

from frappe.tests import IntegrationTestCase

from docusign_integration.exceptions import (
    DocumensoApiError,
    DocumensoAuthenticationError,
    DocumensoRequestError,
)
from docusign_integration.http_client import DocumensoHttpClient


class FakeSettings:
    base_url = "https://documenso.example.com/api/v2"
    request_timeout = 30

    def get_password(self, field):
        return "token-123"


class IntegrationTestDocumensoHttpClient(IntegrationTestCase):
    """Integration tests for DocumensoHttpClient binary request handling."""

    def _make_client(self):
        with patch(
            "docusign_integration.http_client.get_settings",
            return_value=FakeSettings(),
        ):
            client = DocumensoHttpClient()
        client.session = Mock()
        return client

    def _make_response(self, status_code=200, content=b"%PDF-1.4 fake", ok=True, json_body=None):
        if json_body is not None:
            def _json():
                if isinstance(json_body, BaseException):
                    raise json_body
                return json_body
            response = SimpleNamespace(
                status_code=status_code,
                ok=ok,
                content=content,
                json=_json,
            )
        else:
            response = SimpleNamespace(
                status_code=status_code,
                ok=ok,
                content=content,
                json=lambda: (_ for _ in ()).throw(
                    JSONDecodeError("Expecting value", "", 0)
                ),
            )
        return response

    def test_get_binary_returns_bytes(self):
        client = self._make_client()
        response = self._make_response(content=b"%PDF-1.4 signed binary")
        client.session.request.return_value = response

        result = client.get_binary("/api/v2/envelope/item/item_1/download", params={"version": "signed"})

        self.assertEqual(result, b"%PDF-1.4 signed binary")
        client.session.request.assert_called_once()

    def test_get_binary_empty_body_raises_api_error(self):
        client = self._make_client()
        client.session.request.return_value = self._make_response(content=b"")

        with self.assertRaises(DocumensoApiError):
            client.get_binary("/api/v2/envelope/item/item_1/download")

    def test_get_binary_authentication_error(self):
        client = self._make_client()
        client.session.request.return_value = self._make_response(status_code=401, ok=False)

        with self.assertRaises(DocumensoAuthenticationError):
            client.get_binary("/api/v2/envelope/item/item_1/download")

    def test_get_binary_api_error_with_json_message(self):
        client = self._make_client()
        response = self._make_response(
            status_code=404,
            ok=False,
            json_body={"message": "Item not found"},
        )
        client.session.request.return_value = response

        with self.assertRaises(DocumensoApiError) as ctx:
            client.get_binary("/api/v2/envelope/item/item_1/download")
        self.assertIn("Item not found", str(ctx.exception))

    def test_get_binary_api_error_without_json_message(self):
        client = self._make_client()
        response = self._make_response(status_code=500, ok=False)
        client.session.request.return_value = response

        with self.assertRaises(DocumensoApiError) as ctx:
            client.get_binary("/api/v2/envelope/item/item_1/download")
        self.assertIn("500", str(ctx.exception))

    def test_get_binary_network_error(self):
        import requests

        client = self._make_client()
        client.session.request.side_effect = requests.RequestException("boom")

        with self.assertRaises(DocumensoRequestError):
            client.get_binary("/api/v2/envelope/item/item_1/download")

    def test_json_request_still_returns_parsed_dict(self):
        client = self._make_client()
        response = self._make_response(json_body={"status": "COMPLETED"})
        client.session.request.return_value = response

        result = client.get("/api/v2/envelope/env_1")

        self.assertEqual(result, {"status": "COMPLETED"})
