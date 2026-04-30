"""
Pytest configuration and shared fixtures for testing
"""

import pytest
import os
import sys
from datetime import datetime

# Configure test environment
os.environ['FLASK_ENV'] = 'testing'

# Add backend directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, BACKEND_DIR)


@pytest.fixture(scope='session')
def app_context():
    """Create application context for testing"""
    from app import create_app
    
    app = create_app('testing')
    return app


@pytest.fixture
def app_with_db():
    """Fixture providing Flask app and database with clean state"""
    from app import create_app
    from app.extensions import db
    
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app, db
        db.session.remove()
        db.drop_all()


@pytest.fixture
def app(app_with_db):
    """Fixture providing Flask application instance"""
    return app_with_db[0]


@pytest.fixture
def db(app_with_db):
    """Fixture providing database instance"""
    return app_with_db[1]


@pytest.fixture
def client(app):
    """Fixture providing Flask test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Fixture providing CLI test runner"""
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def reset_modules():
    """Reset imported modules between tests to avoid state leakage"""
    yield
    # Cleanup after test


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
