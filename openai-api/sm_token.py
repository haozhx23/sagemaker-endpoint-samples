"""Bearer token + EventStream→SSE transport for SageMaker OpenAI-compatible endpoints."""
from __future__ import annotations

from datetime import timedelta
from typing import Optional

import httpx
from botocore.eventstream import EventStreamBuffer
from sagemaker.core.token_generator import generate_token


def generate_sm_token(region: str, expiry: Optional[timedelta] = None) -> str:
    """Issue a bearer token. Default 5 min validity, max 12 h."""
    return generate_token(region=region, expiry=expiry or timedelta(minutes=5))


class SageMakerAuth(httpx.Auth):
    """Sign every request with a fresh bearer token (no on-disk caching)."""

    def __init__(self, region: str, expiry: Optional[timedelta] = None):
        self.region = region
        self.expiry = expiry

    def auth_flow(self, request: httpx.Request):
        request.headers["Authorization"] = (
            f"Bearer {generate_sm_token(self.region, self.expiry)}"
        )
        yield request


class _SseFromEventStream(httpx.SyncByteStream):
    def __init__(self, inner: httpx.SyncByteStream):
        self._inner = inner
        self._buf = EventStreamBuffer()

    def __iter__(self):
        for chunk in self._inner:
            self._buf.add_data(chunk)
            for event in self._buf:
                yield event.payload

    def close(self):
        self._inner.close()


class SageMakerOpenAITransport(httpx.HTTPTransport):
    """Unwrap AWS EventStream binary framing on text/event-stream responses.

    SageMaker wraps SSE in an AWS EventStream binary frame even when the
    response Content-Type is text/event-stream; without unwrapping, the
    OpenAI SDK's stream parser fails with UnicodeDecodeError. Non-streaming
    responses pass through unchanged.
    """

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        response = super().handle_request(request)
        if "text/event-stream" in response.headers.get("content-type", "").lower():
            response.stream = _SseFromEventStream(response.stream)
        return response
