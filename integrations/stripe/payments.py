"""Create Stripe PaymentIntents for approved agent proposals."""

import logging

from config import get_settings

logger = logging.getLogger(__name__)

# Stripe minimum charge is $0.50
_STRIPE_MIN_CENTS = 50


def create_agent_payment(
    amount_usd: float,
    description: str,
    metadata: dict,
) -> dict:
    """
    Create a confirmed Stripe PaymentIntent for an approved proposal.

    Uses the test payment method pm_card_visa so the charge appears
    immediately on the Stripe test-mode dashboard.

    Returns a dict with payment_intent_id and status, or skipped=True
    if Stripe is not configured or the amount is zero.
    """
    if amount_usd <= 0:
        return {"skipped": True, "reason": "zero_amount"}

    settings = get_settings()
    if not settings.stripe_secret_key:
        logger.warning("Stripe secret key not configured — skipping payment creation")
        return {"skipped": True, "reason": "not_configured"}

    try:
        import stripe
        stripe.api_key = settings.stripe_secret_key

        amount_cents = max(_STRIPE_MIN_CENTS, round(amount_usd * 100))

        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="usd",
            payment_method="pm_card_visa",
            payment_method_types=["card"],
            confirm=True,
            description=description,
            metadata={k: str(v)[:500] for k, v in metadata.items()},
        )

        logger.info(
            "Stripe PaymentIntent created: %s | %s | $%.2f | status=%s",
            intent.id,
            description,
            amount_usd,
            intent.status,
        )
        return {
            "payment_intent_id": intent.id,
            "status": intent.status,
            "amount_usd": amount_usd,
            "amount_cents": amount_cents,
        }

    except Exception as exc:
        logger.error("Stripe payment failed for '%s': %s", description, exc)
        return {"skipped": True, "reason": "stripe_error", "error": str(exc)}
