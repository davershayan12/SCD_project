"""Integration tests for document upload API."""

import io
from pathlib import Path

import pytest


class TestDocumentUpload:
    """Test document upload endpoint."""

    def test_upload_valid_txt(self, client, sample_txt_content):
        """Test uploading a valid text file."""
        files = {
            "file": ("test.txt", io.BytesIO(sample_txt_content.encode()), "text/plain")
        }

        response = client.post("/api/v1/documents", files=files)

        assert response.status_code == 201
        data = response.json()
        assert data["file_type"] == "txt"
        assert data["original_filename"] == "test.txt"
        assert data["total_pages"] == 1
        assert data["total_chars"] > 0
        assert "id" in data

    def test_upload_valid_pdf(self, client, sample_pdf_content):
        """Test uploading a valid PDF file."""
        files = {
            "file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")
        }

        response = client.post("/api/v1/documents", files=files)

        assert response.status_code == 201
        data = response.json()
        assert data["file_type"] == "pdf"
        assert data["original_filename"] == "test.pdf"
        assert data["total_pages"] >= 1

    def test_upload_duplicate_file(self, client, sample_txt_content):
        """Test uploading the same file twice (deduplication)."""
        files = {
            "file": ("test.txt", io.BytesIO(sample_txt_content.encode()), "text/plain")
        }

        # First upload
        response1 = client.post("/api/v1/documents", files=files)
        assert response1.status_code == 201
        doc_id_1 = response1.json()["id"]

        # Second upload of same content
        files = {
            "file": ("test.txt", io.BytesIO(sample_txt_content.encode()), "text/plain")
        }
        response2 = client.post("/api/v1/documents", files=files)

        assert response2.status_code == 201
        data = response2.json()
        assert data["id"] == doc_id_1
        assert "duplicate" in data["message"].lower()

    def test_upload_invalid_extension(self, client):
        """Test uploading file with invalid extension."""
        files = {
            "file": ("test.docx", io.BytesIO(b"content"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        }

        response = client.post("/api/v1/documents", files=files)

        assert response.status_code == 400
        assert "not supported" in response.json()["detail"]

    def test_upload_oversized_file(self, client):
        """Test uploading file that exceeds size limit."""
        # Create a file larger than 50MB
        large_content = b"x" * (51 * 1024 * 1024)
        files = {
            "file": ("large.txt", io.BytesIO(large_content), "text/plain")
        }

        response = client.post("/api/v1/documents", files=files)

        assert response.status_code == 400
        assert "exceeds maximum" in response.json()["detail"]

    def test_upload_corrupt_pdf(self, client):
        """Test uploading corrupt PDF."""
        files = {
            "file": ("corrupt.pdf", io.BytesIO(b"Not a real PDF"), "application/pdf")
        }

        response = client.post("/api/v1/documents", files=files)

        assert response.status_code == 400
        assert "Corrupt" in response.json()["detail"] or "invalid" in response.json()["detail"].lower()


class TestDocumentRetrieval:
    """Test document retrieval endpoints."""

    def test_list_documents_empty(self, client):
        """Test listing documents when none exist."""
        response = client.get("/api/v1/documents")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["documents"]) == 0

    def test_list_documents_with_uploads(self, client, sample_txt_content):
        """Test listing documents after uploads."""
        # Upload a document
        files = {
            "file": ("test.txt", io.BytesIO(sample_txt_content.encode()), "text/plain")
        }
        client.post("/api/v1/documents", files=files)

        # List documents
        response = client.get("/api/v1/documents")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["documents"]) == 1
        assert data["documents"][0]["original_filename"] == "test.txt"

    def test_get_document_detail(self, client, sample_txt_content):
        """Test getting detailed document information."""
        # Upload a document
        files = {
            "file": ("test.txt", io.BytesIO(sample_txt_content.encode()), "text/plain")
        }
        upload_response = client.post("/api/v1/documents", files=files)
        doc_id = upload_response.json()["id"]

        # Get document detail
        response = client.get(f"/api/v1/documents/{doc_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doc_id
        assert len(data["pages"]) > 0
        assert len(data["chunks"]) > 0
        assert "text_preview" in data["pages"][0]
        assert "text_preview" in data["chunks"][0]

    def test_get_nonexistent_document(self, client):
        """Test getting a document that doesn't exist."""
        response = client.get("/api/v1/documents/nonexistent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestDocumentDeletion:
    """Test document deletion endpoint."""

    def test_delete_document(self, client, sample_txt_content):
        """Test deleting a document."""
        # Upload a document
        files = {
            "file": ("test.txt", io.BytesIO(sample_txt_content.encode()), "text/plain")
        }
        upload_response = client.post("/api/v1/documents", files=files)
        doc_id = upload_response.json()["id"]

        # Delete the document
        response = client.delete(f"/api/v1/documents/{doc_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["deleted_id"] == doc_id
        assert "successfully" in data["message"].lower()

        # Verify it's gone
        get_response = client.get(f"/api/v1/documents/{doc_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_document(self, client):
        """Test deleting a document that doesn't exist."""
        response = client.delete("/api/v1/documents/nonexistent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_removes_all_data(self, client, sample_txt_content):
        """Test that deletion removes pages and chunks."""
        # Upload a document
        files = {
            "file": ("test.txt", io.BytesIO(sample_txt_content.encode()), "text/plain")
        }
        upload_response = client.post("/api/v1/documents", files=files)
        doc_id = upload_response.json()["id"]

        # Verify it has pages and chunks
        detail_response = client.get(f"/api/v1/documents/{doc_id}")
        assert len(detail_response.json()["pages"]) > 0
        assert len(detail_response.json()["chunks"]) > 0

        # Delete
        client.delete(f"/api/v1/documents/{doc_id}")

        # Verify it's completely gone
        get_response = client.get(f"/api/v1/documents/{doc_id}")
        assert get_response.status_code == 404
