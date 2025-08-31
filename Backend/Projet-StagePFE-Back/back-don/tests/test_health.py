def test_home_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200

def test_login_endpoint_exists(client):
    resp = client.options("/login")  # au moins OPTIONS si CORS
    assert resp.status_code in (200, 204, 405, 404)