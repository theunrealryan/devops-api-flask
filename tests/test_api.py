import pytest
from app import app as flask_app

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    """Um cliente de teste para a aplicação."""
    return app.test_client()

def test_hello_world(client):
    """Testa o endpoint principal '/'."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Hello World" in response.data
