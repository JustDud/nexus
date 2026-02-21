"""Stripe webhook verification and processing service."""

from dataclasses import dataclass
import hashlib
import hmac
import json
from typing import Any

from integrations.stripe.handlers import StripeEventDispatcher, build_default_dispatcher


class StripeWebhookSignatureError(ValueError):
    """Raised when Stripe signature verification fails."""


@dataclass
class StripeWebhookService:
    webhook_secret: str
    tolerance_seconds: int = 300
    dispatcher: StripeEventDispatcher | None = None

    def __post_init__(self) -> None:
        if not self.webhook_secret:
            raise ValueError("Missing STRIPE_WEBHOOK_SECRET.")
        if self.dispatcher is None:
            self.dispatcher = build_default_dispatcher()

    def _parse_signature_header(self, signature_header: str) -> tuple[int, list[str]]:
        parts = [part.strip() for part in signature_header.split(",") if part.strip()]
        timestamp: int | None = None
        signatures: list[str] = []

        for part in parts:
            key, sep, value = part.partition("=")
            if sep != "=":
                continue
            if key == "t":
                timestamp = int(value)
            elif key == "v1":
                signatures.append(value)

        if timestamp is None or not signatures:
            raise StripeWebhookSignatureError("Malformed Stripe-Signature header.")

        return timestamp, signatures

    def _build_expected_signature(self, payload: bytes, timestamp: int) -> str:
        signed_payload = f"{timestamp}.{payload.decode('utf-8')}".encode("utf-8")
        digest = hmac.new(
            self.webhook_secret.encode("utf-8"),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        return digest

    def verify_signature(
        self,
        payload: bytes,
        signature_header: str | None,
        now_timestamp: int,
    ) -> None:
        if not signature_header:
            raise StripeWebhookSignatureError("Missing Stripe-Signature header.")

        timestamp, signatures = self._parse_signature_header(signature_header)

        if abs(now_timestamp - timestamp) > self.tolerance_seconds:
            raise StripeWebhookSignatureError("Stripe signature timestamp outside tolerance.")

        expected_signature = self._build_expected_signature(payload, timestamp)
        is_valid = any(
            hmac.compare_digest(expected_signature, candidate)
            for candidate in signatures
        )
        if not is_valid:
            raise StripeWebhookSignatureError("Invalid Stripe signature.")

    def parse_event(self, payload: bytes) -> dict[str, Any]:
        try:
            event = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise StripeWebhookSignatureError("Invalid Stripe webhook payload.") from exc

        if not isinstance(event, dict):
            raise StripeWebhookSignatureError("Stripe payload must be a JSON object.")
        return event

    def process_webhook(
        self,
        payload: bytes,
        signature_header: str | None,
        now_timestamp: int,
    ) -> dict[str, Any]:
        self.verify_signature(payload, signature_header, now_timestamp=now_timestamp)
        event = self.parse_event(payload)
        if self.dispatcher is None:
            raise RuntimeError("Stripe dispatcher is not configured.")
        dispatch_result = self.dispatcher.dispatch(event)
        return {
            "received": True,
            "event_id": event.get("id"),
            "event_type": event.get("type"),
            "dispatch": dispatch_result,
        }
