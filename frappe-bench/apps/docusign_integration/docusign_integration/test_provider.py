# Copyright (c) 2026, Ayush Kumar Kashyap and contributors
# For license information, please see license.txt

"""Tests for DocumensoProvider envelope retrieval and signed PDF download."""

from unittest.mock import Mock

from frappe.tests import IntegrationTestCase

from docusign_integration.provider import DocumensoProvider


class IntegrationTestDocumensoProvider(IntegrationTestCase):
    """Integration tests for DocumensoProvider envelope/download operations."""

    def _make_provider(self):
        provider = DocumensoProvider()
        provider.client = Mock()
        return provider

    def test_get_envelope_delegates_to_client(self):
        provider = self._make_provider()
        provider.client.get.return_value = {"status": "COMPLETED"}

        result = provider.get_envelope("envelope_1")

        self.assertEqual(result, {"status": "COMPLETED"})
        provider.client.get.assert_called_once_with("/api/v2/envelope/envelope_1")

    def test_download_envelope_item_delegates_to_binary_client(self):
        provider = self._make_provider()
        provider.client.get_binary.return_value = b"%PDF-1.4 signed"

        result = provider.download_envelope_item("item_1", version="signed")

        self.assertEqual(result, b"%PDF-1.4 signed")
        provider.client.get_binary.assert_called_once_with(
            "/api/v2/envelope/item/item_1/download",
            params={"version": "signed"},
        )
