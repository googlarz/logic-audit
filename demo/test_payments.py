import pytest
from payments import charge_customer


def test_successful_charge():
    result = charge_customer("cus_123", 10.00)
    assert result["status"] == "ok"
    assert "transaction_id" in result
    assert result["amount_charged"] == 1000


def test_card_declined():
    result = charge_customer("cus_456", 50.00)
    assert result["status"] == "error"
    assert result["code"] == "ERR_CARD_DECLINED"


def test_invalid_customer():
    result = charge_customer("", 10.00)
    assert result["status"] == "error"
    assert result["code"] == "ERR_INVALID_CUSTOMER"


def test_amount_in_cents():
    # Verify the function handles cent-denominated amounts
    result = charge_customer("cus_123", 100)
    assert result["amount_charged"] == 100
