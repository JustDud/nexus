"""FastAPI router for Stripe webhook endpoints."""

from functools import lru_cache
import time

from fastapi import APIRouter, Header, HTTPException, Request, status

from config import get_settings
from integrations.stripe.service import StripeWebhookService, StripeWebhookSignatureError

stripe_router = APIRouter(tags=["stripe"])


@lru_cache
def get_stripe_webhook_service() -> StripeWebhookService | None:
    settings = get_settings()
    if not settings.stripe_webhook_secret:
        return None
    return StripeWebhookService(
        webhook_secret=settings.stripe_webhook_secret,
        tolerance_seconds=settings.stripe_webhook_tolerance_seconds,
    )


@stripe_router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
):
    service = get_stripe_webhook_service()
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe webhooks are not configured.",
        )

    payload = await request.body()
    try:
        result = service.process_webhook(
            payload=payload,
            signature_header=stripe_signature,
            now_timestamp=int(time.time()),
        )
    except StripeWebhookSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return result
