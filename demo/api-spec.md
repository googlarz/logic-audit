# Payments API Specification

## POST /charge

Charges a customer via the payment processor.

### Request fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `customer_id` | string | yes | Stripe customer ID |
| `amount` | integer | yes | Amount in **cents** (e.g. 1000 = $10.00) |
| `currency` | string | no | ISO 4217 code. Default: `"usd"` |
| `idempotency_key` | string | no | If provided, duplicate requests within 24 hours return the original response |

### Success response

```json
{
  "status": "ok",
  "transaction_id": "txn_abc123",
  "amount_charged": 1000
}
```

### Error response

```json
{
  "status": "error",
  "code": "ERR_INSUFFICIENT_FUNDS | ERR_CARD_DECLINED | ERR_INVALID_CUSTOMER",
  "message": "Human-readable description"
}
```

### Behavior

- Returns `ERR_INSUFFICIENT_FUNDS` if balance check fails before charge
- Returns `ERR_CARD_DECLINED` if payment processor declines the card
- Returns `ERR_INVALID_CUSTOMER` if `customer_id` is not found
- Maximum **3 retries** on network timeout before returning an error
- Idempotency: duplicate requests with the same `idempotency_key` within 24 hours
  return the original response without re-charging
