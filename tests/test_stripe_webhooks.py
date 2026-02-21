"""Tests for Stripe webhook integration endpoints."""

import hashlib
import hmac
import json
import os
import time

import pytest
from fastapi.testclient import TestClient

from config import get_settings
from integrations.stripe.router import get_stripe_webhook_service
from main import app


def _sign_payload(secret: str, payload: bytes, timestamp: int) -> str:
    signed_payload = f"{timestamp}.{payload.decode('utf-8')}".encode("utf-8")
    digest = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()
    return f"t={timestamp},v1={digest}"


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


class TestStripeWebhooks:
    def teardown_method(self):
        get_settings.cache_clear()
        get_stripe_webhook_service.cache_clear()
        os.environ.pop("STRIPE_WEBHOOK_SECRET", None)

    def test_stripe_webhook_not_configured_returns_503(self, client):
        get_settings.cache_clear()
        get_stripe_webhook_service.cache_clear()
        os.environ.pop("STRIPE_WEBHOOK_SECRET", None)

        resp = client.post("/api/webhooks/stripe", json={"type": "ping"})
        assert resp.status_code == 503
        assert "not configured" in resp.json()["detail"]

    def test_stripe_webhook_missing_signature_returns_400(self, client):
        os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
        get_settings.cache_clear()
        get_stripe_webhook_service.cache_clear()

        resp = client.post("/api/webhooks/stripe", json={"type": "invoice.payment_succeeded"})
        assert resp.status_code == 400
        assert "Missing Stripe-Signature" in resp.json()["detail"]

    def test_stripe_webhook_invalid_signature_returns_400(self, client):
        os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
        get_settings.cache_clear()
        get_stripe_webhook_service.cache_clear()

        payload = json.dumps({"id": "evt_1", "type": "invoice.payment_succeeded"}).encode("utf-8")
        resp = client.post(
            "/api/webhooks/stripe",
            content=payload,
            headers={"Stripe-Signature": "t=123,v1=invalid"},
        )
        assert resp.status_code == 400
        assert "Invalid Stripe signature" in resp.json()["detail"] or "timestamp" in resp.json()["detail"]

    def test_stripe_webhook_valid_signature_returns_200(self, client):
        secret = "whsec_test"
        os.environ["STRIPE_WEBHOOK_SECRET"] = secret
        get_settings.cache_clear()
        get_stripe_webhook_service.cache_clear()

        event = {"id": "evt_123", "type": "invoice.payment_succeeded", "data": {"object": {}}}
        payload = json.dumps(event).encode("utf-8")
        timestamp = int(time.time())
        signature = _sign_payload(secret, payload, timestamp)

        resp = client.post(
            "/api/webhooks/stripe",
            content=payload,
            headers={"Stripe-Signature": signature, "Content-Type": "application/json"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["received"] is True
        assert body["event_id"] == "evt_123"
        assert body["event_type"] == "invoice.payment_succeeded"
        assert body["dispatch"]["handled"] is True
