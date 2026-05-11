"""Pytest configuration for app tests (asyncio + aiohttp)."""

from __future__ import annotations

import pytest_asyncio
from aiohttp.test_utils import TestClient, TestServer


@pytest_asyncio.fixture
async def aiohttp_client():
    clients: list[TestClient] = []

    async def make_client(app):
        client = TestClient(TestServer(app))
        await client.start_server()
        clients.append(client)
        return client

    yield make_client

    for client in clients:
        await client.close()
