import os
import tempfile
import pytest

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.environ["DB_PATH"] = db_path
    import importlib, app as app_module
    importlib.reload(app_module)
    from app import app, init_db
    app.config["TESTING"] = True
    with app.test_client() as c:
        init_db()
        yield c
    os.close(db_fd)
    try:
        os.unlink(db_path)
    except PermissionError:
        pass

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "healthy"

def test_list_empty(client):
    res = client.get("/appointments")
    assert res.status_code == 200
    assert res.get_json() == []

def test_create_appointment(client):
    data = {"patient": "John Doe", "doctor": "Dr. Smith", "date": "2026-05-20", "reason": "Checkup"}
    res = client.post("/appointments", json=data)
    assert res.status_code == 201
    assert res.get_json()["patient"] == "John Doe"

def test_create_missing_fields(client):
    data = {"patient": "John Doe"}
    res = client.post("/appointments", json=data)
    assert res.status_code == 400

def test_get_single(client):
    data = {"patient": "Alice", "doctor": "Dr. Jones", "date": "2026-05-21"}
    created = client.post("/appointments", json=data).get_json()
    res = client.get(f"/appointments/{created['id']}")
    assert res.status_code == 200
    assert res.get_json()["patient"] == "Alice"

def test_get_not_found(client):
    res = client.get("/appointments/999")
    assert res.status_code == 404

def test_update_status(client):
    data = {"patient": "Bob", "doctor": "Dr. Adams", "date": "2026-05-22"}
    created = client.post("/appointments", json=data).get_json()
    res = client.patch(f"/appointments/{created['id']}", json={"status": "completed"})
    assert res.status_code == 200
    assert res.get_json()["status"] == "completed"

def test_update_invalid_status(client):
    data = {"patient": "Bob", "doctor": "Dr. Adams", "date": "2026-05-22"}
    created = client.post("/appointments", json=data).get_json()
    res = client.patch(f"/appointments/{created['id']}", json={"status": "invalid_status"})
    assert res.status_code == 400

def test_delete(client):
    data = {"patient": "Charlie", "doctor": "Dr. Evans", "date": "2026-05-23"}
    created = client.post("/appointments", json=data).get_json()
    res = client.delete(f"/appointments/{created['id']}")
    assert res.status_code == 200

def test_filter_by_doctor(client):
    client.post("/appointments", json={"patient": "P1", "doctor": "Dr. X", "date": "2026-05-24"})
    client.post("/appointments", json={"patient": "P2", "doctor": "Dr. Y", "date": "2026-05-25"})
    res = client.get("/appointments?doctor=Dr. X")
    assert res.status_code == 200
    assert len(res.get_json()) == 1
