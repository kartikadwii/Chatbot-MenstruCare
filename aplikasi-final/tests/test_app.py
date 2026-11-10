import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_halaman_utama(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"MenstruCare" in response.data


def test_halaman_chat(client):
    response = client.get("/chat")

    assert response.status_code == 200
    assert b"MenstruCare" in response.data


def test_halaman_admin(client):
    response = client.get("/admin")

    assert response.status_code == 200
    assert b"Dashboard Admin" in response.data


def test_halaman_tidak_ditemukan(client):
    response = client.get("/halaman-tidak-ada")

    assert response.status_code == 404


def test_api_chat(client):
    response = client.post(
        "/api/chat",
        json={"message": "Halo"}
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert "reply" in data
    assert "intent" in data
    assert "score" in data


def test_api_chat_pesan_kosong(client):
    response = client.post(
        "/api/chat",
        json={"message": ""}
    )

    assert response.status_code == 400


def test_api_chat_tanpa_pesan(client):
    response = client.post(
        "/api/chat",
        json={}
    )

    assert response.status_code == 400


def test_api_chat_pesan_terlalu_panjang(client):
    response = client.post(
        "/api/chat",
        json={"message": "a" * 1001}
    )

    assert response.status_code == 400


def test_api_history(client):
    response = client.get("/api/history")

    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert "history" in data


def test_api_clear(client):
    response = client.post("/api/clear")

    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True


def test_api_admin_stats(client):
    response = client.get("/api/admin/stats")

    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert "summary" in data
    assert "intents" in data
    assert "unknown_questions" in data