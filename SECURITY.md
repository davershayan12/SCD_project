# Security Policy

## Supported Versions

ResearchRadar is currently in active development. Security updates will be provided for the latest release.

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public issue
2. Email the maintainers with details
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you to address the issue.

## Security Considerations

ResearchRadar processes uploaded documents and runs AI models locally. Key security measures:

- **File validation**: Extension, MIME type, size, and content verification
- **No code execution**: Uploaded files are never executed
- **Path traversal protection**: Random storage names, no user-controlled paths
- **Local processing**: No data sent to third parties by default
- **Rate limiting**: Applied to prevent abuse
- **Authorization**: Document and report access restricted to owners
- **Secrets management**: Use `.env` files (never committed to git)
- **No sensitive data in logs**: Document text and prompts are not logged

## Known Limitations

- No built-in multi-user authentication in MVP (integrate with existing auth)
- Scanned PDFs with OCR are not supported yet
- Open-source checker cannot access paywalled journals or private corpora
