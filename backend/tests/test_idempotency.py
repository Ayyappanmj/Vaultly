from datetime import datetime, timezone


def test_idempotent_receipt_creation(client, auth_headers):
    idempotency_key = "idemp-key-test-12345"
    payload = {
        "merchant_name": "Idempotent Merchant",
        "purchase_date": datetime.now(timezone.utc).isoformat(),
        "total_amount": 99.99,
        "currency": "USD",
    }

    # First call
    res1 = client.post(
        "/api/v1/receipts",
        headers={**auth_headers, "Idempotency-Key": idempotency_key},
        json=payload,
    )
    assert res1.status_code == 201
    receipt_id = res1.json()["id"]

    # Second call with same key and payload returns cached response
    res2 = client.post(
        "/api/v1/receipts",
        headers={**auth_headers, "Idempotency-Key": idempotency_key},
        json=payload,
    )
    assert res2.status_code == 201
    assert res2.json()["id"] == receipt_id
    assert res2.json()["merchant_name"] == "Idempotent Merchant"

    # Third call with same key but DIFFERENT payload returns 409 Conflict!
    different_payload = {**payload, "total_amount": 500.00}
    res3 = client.post(
        "/api/v1/receipts",
        headers={**auth_headers, "Idempotency-Key": idempotency_key},
        json=different_payload,
    )
    assert res3.status_code == 409
    assert "different request payload" in res3.json()["detail"]
