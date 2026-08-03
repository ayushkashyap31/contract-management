import json
from typing import Any

from docusign_integration.http_client import DocumensoHttpClient


class DocumensoProvider:
    """Provider layer for the Documenso API."""

    def __init__(self):
        self.client = DocumensoHttpClient()

    def create_document(
        self,
        payload: dict[str, Any],
        pdf_content: bytes,
    ) -> dict[str, Any]:
        """Create a document in Documenso and upload the PDF."""

        title = str(payload.get("title") or "document")

        return self.client.post(
            "/api/v2/envelope/create",
            data={"payload": json.dumps(payload)},
            files={"files": (f"{title}.pdf", pdf_content, "application/pdf")},
        )

    def distribute_document(
        self,
        envelope_id: str,
    ) -> dict[str, Any] | list[Any] | None:
        """Distribute an envelope to its recipients for signing.

        Transitions the document from Draft to Pending inside Documenso
        and triggers the signing workflow for all assigned recipients.

        Args:
            envelope_id: The Documenso document/envelope ID.

        Returns:
            Parsed API response containing recipient signing URLs.
        """

        return self.client.post(
            "/api/v2/envelope/distribute",
            json={"envelopeId": envelope_id},
        )

    def verify_connection(self) -> dict[str, Any] | list[Any] | None:
        """Verify connectivity and authentication with the Documenso API."""
        return self.client.get(
            "/api/v1/documents",
            params={"page": 1, "perPage": 1},
        )
