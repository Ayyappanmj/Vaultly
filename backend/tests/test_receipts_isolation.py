from datetime import datetime, timezone


def test_user_data_isolation(client, auth_headers, other_auth_headers):
    # User A creates a receipt
    create_res = client.post(
        "/api/v1/receipts",
        headers=auth_headers,
        json={
            "merchant_name": "Private Store A",
            "purchase_date": datetime.now(timezone.utc).isoformat(),
            "total_amount": 150.00,
            "currency": "USD",
            "items": [
                {"description": "Private Gadget", "total_price": 150.00, "quantity": 1}
            ],
        },
    )
    assert create_res.status_code == 201
    receipt_id = create_res.json()["id"]

    # User A can read it
    get_res = client.get(f"/api/v1/receipts/{receipt_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["merchant_name"] == "Private Store A"

    # User B CANNOT read it (404/isolation)
    other_res = client.get(f"/api/v1/receipts/{receipt_id}", headers=other_auth_headers)
    assert other_res.status_code == 404

    # User B cannot update it
    other_update = client.put(
        f"/api/v1/receipts/{receipt_id}",
        headers=other_auth_headers,
        json={"merchant_name": "Hacked"},
    )
    assert other_update.status_code == 404

    # User B cannot delete it
    other_del = client.delete(
        f"/api/v1/receipts/{receipt_id}", headers=other_auth_headers
    )
    assert other_del.status_code == 404


def test_soft_delete(client, auth_headers):
    create_res = client.post(
        "/api/v1/receipts",
        headers=auth_headers,
        json={
            "merchant_name": "Store to Delete",
            "purchase_date": datetime.now(timezone.utc).isoformat(),
            "total_amount": 50.00,
            "currency": "USD",
        },
    )
    receipt_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/receipts/{receipt_id}", headers=auth_headers)
    assert del_res.status_code == 200

    # Getting soft-deleted receipt returns 404
    get_res = client.get(f"/api/v1/receipts/{receipt_id}", headers=auth_headers)
    assert get_res.status_code == 404


def test_receipts_filtering_and_pagination(client, auth_headers):
    for i in range(5):
        client.post(
            "/api/v1/receipts",
            headers=auth_headers,
            json={
                "merchant_name": f"Coffee Shop {i}",
                "purchase_date": datetime.now(timezone.utc).isoformat(),
                "total_amount": 10.00 + i,
                "currency": "USD",
            },
        )

    res = client.get("/api/v1/receipts?page=1&page_size=3", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 3
    assert data["total"] == 5
    assert data["total_pages"] == 2
