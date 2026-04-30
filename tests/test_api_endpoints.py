"""
Unit tests for Flask application routes and API endpoints
"""

import pytest
import json
from datetime import datetime


class TestAPIEndpoints:
    """Test API endpoints and routing"""
    
    def test_health_endpoint_returns_json(self, client):
        """Test health endpoint returns proper JSON"""
        response = client.get('/health')
        
        assert response.status_code == 200
        assert response.is_json
        data = response.get_json()
        assert isinstance(data, dict)
    
    def test_health_endpoint_response_structure(self, client):
        """Test health endpoint response has required fields"""
        response = client.get('/health')
        data = response.get_json()
        
        required_fields = ['status', 'service', 'timestamp']
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"


class TestContentType:
    """Test content type headers"""
    
    def test_api_returns_json_content_type(self, client):
        """Test API endpoints return JSON content type"""
        response = client.get('/health')
        
        assert 'application/json' in response.content_type


class TestTimeouts:
    """Test timeout handling"""
    
    def test_endpoint_responds_in_reasonable_time(self, client):
        """Test endpoint responds quickly"""
        import time
        
        start = time.time()
        response = client.get('/health')
        elapsed = time.time() - start
        
        # Health check should respond in less than 1 second
        assert elapsed < 1.0
        assert response.status_code == 200


class TestErrorResponse:
    """Test error response formats"""
    
    def test_invalid_endpoint_returns_error(self, client):
        """Test invalid endpoint returns appropriate error"""
        response = client.get('/invalid-endpoint-12345')
        
        assert response.status_code == 404


@pytest.fixture
def client(app_with_db):
    """Fixture providing test client"""
    app, _ = app_with_db
    return app.test_client()


@pytest.fixture
def app_with_db():
    """Fixture providing Flask app and database"""
    from app import create_app
    from app.extensions import db
    
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app, db
        db.session.remove()
        db.drop_all()
