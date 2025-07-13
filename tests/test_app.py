import sys
sys.path.insert(0, '/home/alexandrosanastasiou/workspace/xeri')
import pytest
import os
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
from app import app, db, User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_index(client):
    rv = client.get('/')
    assert rv.status_code == 200
