"""
Fixtures for production smoke tests.
Run: PROD_URL=https://example.com pytest tests/prod/ -v
"""
import os

import httpx
import pytest

PROD_URL = os.environ.get("PROD_URL", "").rstrip("/")


@pytest.fixture(scope="session")
def prod_url():
    if not PROD_URL:
        pytest.skip("PROD_URL not set")
    return PROD_URL


@pytest.fixture(scope="session")
def prod_client(prod_url):
    """HTTP client for production API requests."""
    with httpx.Client(base_url=prod_url, timeout=15.0) as client:
        yield client
