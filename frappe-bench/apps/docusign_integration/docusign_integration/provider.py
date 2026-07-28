from typing import Any

import requests as requests_lib

from docusign_integration.exceptions import DocumensoRequestError
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

        response = self.client.post("/api/v1/documents", json=payload)
        self._upload_document(response["uploadUrl"], pdf_content)
        return response

    def _upload_document(
        self,
        upload_url: str,
        pdf_content: bytes,
    ) -> None:
        """Upload PDF bytes to the presigned S3 URL."""

        try:
            upload_response = requests_lib.put(
                upload_url,
                data=pdf_content,
                headers={"Content-Type": "application/octet-stream"},
            )
            upload_response.raise_for_status()
        except requests_lib.RequestException as exc:
            raise DocumensoRequestError(
                "Failed to upload document to Documenso."
            ) from exc

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
