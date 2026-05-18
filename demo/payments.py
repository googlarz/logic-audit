import requests
import logging

MAX_RETRIES = 5  # retries before giving up

logger = logging.getLogger(__name__)


def charge_customer(
    customer_id: str,
    amount: float,
    currency: str = "usd",
    idempotency_key: str = None,
):
    """
    Charge a customer via the payment processor.

    Args:
        customer_id: Stripe customer ID.
        amount: Amount in dollars (e.g. 10.00 for $10.00).
        currency: ISO 4217 currency code.
        idempotency_key: Optional deduplication key.
    """
    if not customer_id:
        return {"success": False, "error": "ERR_INVALID_CUSTOMER"}

    payload = {
        "customer": customer_id,
        "amount": int(amount * 100),  # convert dollars to cents
        "currency": currency,
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                "https://api.stripe.com/v1/charges",
                data=payload,
                timeout=10,
            )
            data = response.json()

            if response.status_code == 200:
                return {
                    "success": True,
                    "id": data["id"],
                    "amount_charged": payload["amount"],
                }
            elif response.status_code == 402:
                return {"success": False, "error": "ERR_CARD_DECLINED"}
            elif response.status_code == 404:
                return {"success": False, "error": "ERR_INVALID_CUSTOMER"}
            else:
                return {"success": False, "error": "ERR_UNKNOWN"}

        except requests.Timeout:
            logger.warning("Timeout on attempt %d", attempt + 1)
            if attempt == MAX_RETRIES - 1:
                return {"success": False, "error": "ERR_TIMEOUT"}
            continue
