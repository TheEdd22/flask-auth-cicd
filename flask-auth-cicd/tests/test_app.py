import pytest
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app import app, db


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


def test_health_check(client):
    res = client.get('/health')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['status'] == 'healthy'


def test_register_user(client):
    payload = {'username': 'testuser', 'email': 'test@test.com', 'password': 'secret123'}
    res = client.post('/api/register', json=payload)
    assert res.status_code == 201
    data = json.loads(res.data)
    assert data['user']['username'] == 'testuser'


def test_register_duplicate_username(client):
    payload = {'username': 'testuser', 'email': 'test@test.com', 'password': 'secret123'}
    client.post('/api/register', json=payload)
    payload2 = {'username': 'testuser', 'email': 'other@test.com', 'password': 'pass'}
    res = client.post('/api/register', json=payload2)
    assert res.status_code == 409


def test_login_success(client):
    client.post('/api/register', json={'username': 'user1', 'email': 'u@u.com', 'password': 'pass123'})
    res = client.post('/api/login', json={'username': 'user1', 'password': 'pass123'})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert 'access_token' in data


def test_login_invalid_credentials(client):
    res = client.post('/api/login', json={'username': 'nouser', 'password': 'wrong'})
    assert res.status_code == 401


def test_profile_requires_auth(client):
    res = client.get('/api/profile')
    assert res.status_code == 401


def test_profile_with_token(client):
    client.post('/api/register', json={'username': 'authuser', 'email': 'a@a.com', 'password': 'pass'})
    login_res = client.post('/api/login', json={'username': 'authuser', 'password': 'pass'})
    token = json.loads(login_res.data)['access_token']
    res = client.get('/api/profile', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 200
    assert json.loads(res.data)['user']['username'] == 'authuser'


def test_register_missing_fields(client):
    res = client.post('/api/register', json={'username': 'only'})
    assert res.status_code == 400
