# API Reference

**Version:** 0.1.0  
**Base URL:** `http://localhost:8000`

---

## Documents API

### Upload Document

**Endpoint:** `POST /api/v1/documents`  
**Description:** Upload and process a PDF or TXT document

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (PDF or TXT file)

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "filename": "random-hash.pdf",
  "original_filename": "document.pdf",
  "file_type": "pdf",
  "file_size_bytes": 123456,
  "total_pages": 10,
  "total_chars": 50000,
  "created_at": "2026-11-21T08:00:00Z",
  "message": "Document uploaded and processed successfully"
}
```

**Errors:**
- `400 Bad Request`: Invalid file type, size exceeded, corrupt PDF, scanned PDF
- `500 Internal Server Error`: Processing failed

**Notes:**
- Duplicate files (same hash) return existing document with message noting duplicate
- Page numbers and character offsets are preserved through extraction
- Text is normalized (ligatures, hyphenation, whitespace)
- Chunks are created for later matching

---

### List Documents

**Endpoint:** `GET /api/v1/documents`  
**Description:** List all documents for current user

**Response:** `200 OK`
```json
{
  "documents": [
    {
      "id": "uuid",
      "filename": "random-hash.pdf",
      "original_filename": "document.pdf",
      "file_type": "pdf",
      "file_size_bytes": 123456,
      "total_pages": 10,
      "created_at": "2026-11-21T08:00:00Z"
    }
  ],
  "total": 1
}
```

---

### Get Document Detail

**Endpoint:** `GET /api/v1/documents/{document_id}`  
**Description:** Get detailed information about a document

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "filename": "random-hash.pdf",
  "original_filename": "document.pdf",
  "file_type": "pdf",
  "file_size_bytes": 123456,
  "total_pages": 10,
  "total_chars": 50000,
  "owner_id": "default_user",
  "created_at": "2026-11-21T08:00:00Z",
  "pages": [
    {
      "page_number": 1,
      "char_count": 5000,
      "text_preview": "First 200 characters..."
    }
  ],
  "chunks": [
    {
      "chunk_index": 0,
      "page_number": 1,
      "char_start": 0,
      "char_end": 256,
      "token_count": 65,
      "text_preview": "First 100 characters..."
    }
  ]
}
```

**Errors:**
- `404 Not Found`: Document does not exist
- `403 Forbidden`: Not authorized to access document

---

### Delete Document

**Endpoint:** `DELETE /api/v1/documents/{document_id}`  
**Description:** Delete a document and all associated data

**Response:** `200 OK`
```json
{
  "message": "Document deleted successfully",
  "deleted_id": "uuid"
}
```

**Notes:**
- Removes document record, pages, chunks, and stored file
- Cascading delete ensures no orphaned data

**Errors:**
- `404 Not Found`: Document does not exist
- `403 Forbidden`: Not authorized to delete document

---

## Health Check

**Endpoint:** `GET /health`  
**Description:** Check API health status

**Response:** `200 OK`
```json
{
  "status": "healthy"
}
```

---

## Root

**Endpoint:** `GET /`  
**Description:** API information

**Response:** `200 OK`
```json
{
  "name": "ResearchRadar API",
  "version": "0.1.0",
  "status": "running",
  "docs": "/docs"
}
```

---

## Interactive Documentation

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## Phase 1 Status

✅ **Implemented:**
- Document upload with validation
- PDF and TXT extraction
- Text normalization
- Chunking with page preservation
- Deduplication by hash
- Authorization checks (default_user)
- Error handling

⏳ **Not Yet Implemented:**
- Embeddings (Phase 3)
- Vector storage (Phase 3)
- Plagiarism matching (Phase 2)
- Gap analysis (Phase 4-5)
- Multi-user authentication (future)
