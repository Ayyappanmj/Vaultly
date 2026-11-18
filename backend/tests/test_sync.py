import uuid


def test_sync_batch_idempotency_and_conflicts(client, auth_headers):
    receipt_id = str(uuid.uuid4())
    op_id = "op-sync-100"

    # 1. Sync Create Operation
    create_op = {
        "client_id": "mobile-device-1",
        "operations": [
            {
                "operation_id": op_id,
                "entity_type": "receipt",
                "action": "CREATE",
                "entity_id": receipt_id,
                "client_version": 1,
                "timestamp": "2024-06-01T12:00:00Z",
                "payload": {
                    "merchant_name": "Mobile Synced Coffee",
                    "total_amount": "4.75",
                    "purchase_date": "2024-06-01T10:00:00Z",
                },
            }
        ],
    }

    res1 = client.post("/api/v1/sync", headers=auth_headers, json=create_op)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["processed_count"] == 1
    assert data1["results"][0]["status"] == "SYNCED"

    # 2. Duplicate Sync Create Operation -> must NOT duplicate and must return SYNCED
    res2 = client.post("/api/v1/sync", headers=auth_headers, json=create_op)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["results"][0]["status"] == "SYNCED"

    # 3. Simulate Server Update (bumps server sync_version to 2)
    client.put(
        f"/api/v1/receipts/{receipt_id}",
        headers=auth_headers,
        json={"merchant_name": "Server Updated Coffee"},
    )

    # 4. Mobile sends UPDATE with outdated client_version=1 -> CONFLICT detected!
    conflict_op = {
        "client_id": "mobile-device-1",
        "operations": [
            {
                "operation_id": "op-sync-101",
                "entity_type": "receipt",
                "action": "UPDATE",
                "entity_id": receipt_id,
                "client_version": 1,
                "timestamp": "2024-06-01T13:00:00Z",
                "payload": {"merchant_name": "Conflicting Mobile Name"},
            }
        ],
    }

    res3 = client.post("/api/v1/sync", headers=auth_headers, json=conflict_op)
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["results"][0]["status"] == "CONFLICT"
    assert (
        data3["results"][0]["server_data"]["merchant_name"] == "Server Updated Coffee"
    )
