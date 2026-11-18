def test_register_success(client):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@vaultly.app",
            "password": "SecurePassword1!",
            "full_name": "New User",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "newuser@vaultly.app"
    assert "id" in data


def test_register_weak_password_fails(client):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@vaultly.app",
            "password": "weak",
            "full_name": "Weak User",
        },
    )
    assert res.status_code in {400, 422}


def test_login_success(client, test_user):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@vaultly.app", "password": "Password123!"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_invalid_password(client, test_user):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@vaultly.app", "password": "WrongPassword!"},
    )
    assert res.status_code == 401


def test_refresh_token_rotation(client, test_user):
    # 1. Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@vaultly.app", "password": "Password123!"},
    )
    refresh_1 = login_res.json()["refresh_token"]

    # 2. Refresh
    ref_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_1})
    assert ref_res.status_code == 200
    refresh_2 = ref_res.json()["refresh_token"]
    assert refresh_2 != refresh_1

    # 3. Old refresh token reuse MUST fail
    reuse_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_1})
    assert reuse_res.status_code == 401
    assert "Security breach detected" in reuse_res.json()["detail"]


def test_get_me(client, auth_headers):
    res = client.get("/api/v1/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["email"] == "testuser@vaultly.app"
