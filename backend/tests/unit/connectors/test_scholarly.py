"""Tests for scholarly API connectors."""

import pytest
from app.services.connectors.scholarly import ScholarlySearchService


def test_scholarly_search_service_init():
    service = ScholarlySearchService()
    assert service is not None
