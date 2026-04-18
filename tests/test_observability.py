"""Readiness, Prometheus metrics exposure, and unified JSON error shape (including request_id)."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_ready_returns_database_ok():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.get('/ready')
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'ready'
    assert body['checks']['database']['ok'] is True


@pytest.mark.asyncio
async def test_metrics_endpoint_exposes_prometheus():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.get('/metrics')
    assert response.status_code == 200
    text = response.text
    assert 'http_requests' in text or 'http_request' in text


@pytest.mark.asyncio
async def test_validation_error_includes_request_id():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.post('/auth/register', json={'invalid': True})
    assert response.status_code == 422
    body = response.json()
    assert body['detail'] == 'Validation error'
    assert 'request_id' in body and body['request_id']
    assert body.get('code') == 'validation_error'


@pytest.mark.asyncio
async def test_stats_requires_auth():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.get('/stats')
    assert response.status_code == 401
    body = response.json()
    assert 'detail' in body
    assert body.get('code') == 'http_401'
