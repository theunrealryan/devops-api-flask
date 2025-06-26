import pytest
from app import app, tasks

@pytest.fixture(autouse=True)
def clear_tasks():
    tasks.clear()

def test_empty_list():
    client = app.test_client()
    resp = client.get("/tasks")
    assert resp.get_json() == []

def test_add_task():
    client = app.test_client()
    new_task = {"id": 1, "title": "Teste"}
    resp = client.post("/tasks", json=new_task)
    assert resp.status_code == 201
    assert resp.get_json() == {"msg": "ok"}

    resp2 = client.get("/tasks")
    assert resp2.status_code == 200
    assert resp2.get_json() == [new_task]
