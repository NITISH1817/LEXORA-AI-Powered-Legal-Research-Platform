from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

def test_register_and_login():
    # Attempt to register
    register_response = client.post("/api/auth/register", json={
        "email": "test_auth_user@example.com",
        "password": "securepassword123",
        "full_name": "Test Auth User"
    })
    
    # If already registered, it returns 400. We just want to ensure we can login.
    assert register_response.status_code in (200, 400)
    
    # Attempt to login
    login_response = client.post("/api/auth/login", data={
        "username": "test_auth_user@example.com",
        "password": "securepassword123"
    })
    
    assert login_response.status_code == 200
    token = login_response.json().get("access_token")
    assert token is not None
    
    # Attempt to access me
    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "test_auth_user@example.com"
    
def test_unauthorized_access():
    # Attempt to access protected route without token
    response = client.get("/api/research")
    assert response.status_code == 401
