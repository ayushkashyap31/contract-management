from typing import Any

from docusign_integration.http_client import DocumensoHttpClient


class DocumensoProvider:
    """Provider layer for the Documenso API."""

    def __init__(self):
        self.client = DocumensoHttpClient()

    def create_document(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a document in Documenso and return the API response."""
        return self.client.post("/api/v1/documents", json=payload)
