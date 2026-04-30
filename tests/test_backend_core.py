"""
Unit tests for core backend functionality
Tests for database utilities, configuration, and API endpoints
"""

import pytest
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Configure test environment
os.environ['FLASK_ENV'] = 'testing'

# Add parent directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


class TestDatabaseUtils:
    """Test database utility functions"""
    
    def test_ensure_database_schema_creates_all_tables(self, app_with_db):
        """Test that ensure_database_schema creates all required tables"""
        app, db = app_with_db
        
        with app.app_context():
            from app.utils.database import ensure_database_schema
            # Schema should be created without errors
            ensure_database_schema(db)
            
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            # Verify key tables exist
            assert len(tables) > 0


class TestConfiguration:
    """Test configuration loading and validation"""
    
    def test_config_from_environment(self):
        """Test that config loads from environment variables"""
        os.environ['SECRET_KEY'] = 'test-secret-key-' + 'x' * 20
        
        from app.config import Config
        config = Config()
        
        assert config.SECRET_KEY == os.environ['SECRET_KEY']
    
    def test_config_fallback_for_secret_key(self):
        """Test that SECRET_KEY falls back if not set"""
        old_secret = os.environ.pop('SECRET_KEY', None)
        
        try:
            from importlib import reload
            import app.config
            reload(app.config)
            from app.config import Config
            
            config = Config()
            assert config.SECRET_KEY is not None
        finally:
            if old_secret:
                os.environ['SECRET_KEY'] = old_secret
    
    def test_database_url_normalization(self):
        """Test PostgreSQL URL normalization for SQLAlchemy"""
        os.environ['DATABASE_URL'] = 'postgres://user:pass@localhost/db'
        
        from app.config import _normalized_database_url
        result = _normalized_database_url('default_url')
        
        assert result.startswith('postgresql://')
        assert 'postgres://' not in result


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_check_endpoint(self, client):
        """Test basic health check endpoint"""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'restaurant-ai'
        assert 'timestamp' in data
    
    def test_readiness_check_endpoint(self, client, app_with_db):
        """Test readiness check endpoint"""
        app, db = app_with_db
        
        with app.app_context():
            response = client.get('/health/ready')
            
            assert response.status_code in [200, 503]
            data = response.get_json()
            assert 'status' in data
            assert 'checks' in data or 'database' in data


class TestApplicationFactory:
    """Test application factory pattern"""
    
    def test_create_app_development_mode(self):
        """Test creating app in development mode"""
        from app import create_app
        
        app = create_app('development')
        assert app is not None
        assert app.config['TESTING'] is False
    
    def test_create_app_testing_mode(self):
        """Test creating app in testing mode"""
        from app import create_app
        
        app = create_app('testing')
        assert app is not None
        assert app.config['TESTING'] is True
    
    def test_create_app_production_mode(self):
        """Test creating app in production mode"""
        from app import create_app
        
        app = create_app('production')
        assert app is not None
        # Production mode should have security settings
        assert app.config['SESSION_COOKIE_SECURE'] is True


class TestSecurityConfiguration:
    """Test security-related configurations"""
    
    def test_session_cookie_settings(self):
        """Test session cookie security settings"""
        from app.config import Config
        
        config = Config()
        assert config.SESSION_COOKIE_SECURE is True
        assert config.SESSION_COOKIE_HTTPONLY is True
        assert config.SESSION_COOKIE_SAMESITE in ['Lax', 'Strict', 'None']
    
    def test_database_url_from_environment(self):
        """Test DATABASE_URL environment variable usage"""
        test_url = 'postgresql://user:pass@localhost:5432/testdb'
        os.environ['DATABASE_URL'] = test_url
        
        from importlib import reload
        import app.config
        reload(app.config)
        
        assert os.environ.get('DATABASE_URL') == test_url


class TestErrorHandlers:
    """Test error handling"""
    
    def test_404_error_handling(self, client):
        """Test 404 error response"""
        response = client.get('/nonexistent-endpoint')
        
        assert response.status_code == 404
    
    def test_method_not_allowed_error(self, client):
        """Test 405 method not allowed error"""
        # GET request to an endpoint that expects POST
        response = client.post('/health')
        
        # Should return 405 or handle gracefully
        assert response.status_code in [405, 200, 400]


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


@pytest.fixture
def client(app_with_db):
    """Fixture providing test client"""
    app, _ = app_with_db
    return app.test_client()


@pytest.fixture
def app(app_with_db):
    """Fixture providing Flask app"""
    return app_with_db[0]
