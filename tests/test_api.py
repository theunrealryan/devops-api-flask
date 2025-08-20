import pytest
from app import app as flask_app

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    """Um cliente de teste para a aplicação."""
    return app.test_client()

def test_get_tasks(client):
    """Testa o endpoint para obter todas as tarefas ('/tasks')."""
    response = client.get('/tasks')
    assert response.status_code == 200
    assert response.is_json
    json_data = response.get_json()
    assert "tasks" in json_data
