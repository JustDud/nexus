"""Stripe webhook event handler registry."""

from collections.abc import Callable
from dataclasses import dataclass, field
import logging
from typing import Any

logger = logging.getLogger(__name__)

StripeEvent = dict[str, Any]
StripeHandler = Callable[[StripeEvent], dict[str, Any]]


def _default_handler(event: StripeEvent) -> dict[str, Any]:
    event_type = event.get("type", "unknown")
    logger.info("Unhandled Stripe event received: %s", event_type)
    return {"handled": False, "event_type": event_type}


@dataclass
class StripeEventDispatcher:
    """Simple event-type to handler dispatcher."""

    handlers: dict[str, StripeHandler] = field(default_factory=dict)
    fallback_handler: StripeHandler = _default_handler

    def register(self, event_type: str, handler: StripeHandler) -> None:
        self.handlers[event_type] = handler

    def dispatch(self, event: StripeEvent) -> dict[str, Any]:
        event_type = str(event.get("type", ""))
        handler = self.handlers.get(event_type, self.fallback_handler)
        return handler(event)


def _handle_checkout_completed(event: StripeEvent) -> dict[str, Any]:
    logger.info("Stripe checkout completed: id=%s", event.get("id"))
    return {"handled": True, "event_type": "checkout.session.completed"}


def _handle_payment_succeeded(event: StripeEvent) -> dict[str, Any]:
    logger.info("Stripe invoice payment succeeded: id=%s", event.get("id"))
    return {"handled": True, "event_type": "invoice.payment_succeeded"}


def _handle_payment_failed(event: StripeEvent) -> dict[str, Any]:
    logger.info("Stripe invoice payment failed: id=%s", event.get("id"))
    return {"handled": True, "event_type": "invoice.payment_failed"}


def _handle_subscription_deleted(event: StripeEvent) -> dict[str, Any]:
    logger.info("Stripe subscription deleted: id=%s", event.get("id"))
    return {"handled": True, "event_type": "customer.subscription.deleted"}


def _handle_payment_intent_succeeded(event: StripeEvent) -> dict[str, Any]:
    logger.info("Stripe payment intent succeeded: id=%s", event.get("id"))
    return {"handled": True, "event_type": "payment_intent.succeeded"}


def build_default_dispatcher() -> StripeEventDispatcher:
    dispatcher = StripeEventDispatcher()
    dispatcher.register("checkout.session.completed", _handle_checkout_completed)
    dispatcher.register("invoice.payment_succeeded", _handle_payment_succeeded)
    dispatcher.register("invoice.payment_failed", _handle_payment_failed)
    dispatcher.register("customer.subscription.deleted", _handle_subscription_deleted)
    dispatcher.register("payment_intent.succeeded", _handle_payment_intent_succeeded)
    return dispatcher
