"""
Unit tests for utility functions and helpers
"""

import pytest
import os
from datetime import datetime, timedelta


class TestDatabaseURLParsing:
    """Test database URL parsing and normalization"""
    
    def test_normalize_postgres_url(self):
        """Test normalization of postgres:// to postgresql://"""
        from app.config import _normalized_database_url
        
        postgres_url = 'postgres://user:pass@localhost:5432/db'
        result = _normalized_database_url(postgres_url)
        
        assert result.startswith('postgresql://')
        assert 'postgres://' not in result
    
    def test_preserve_postgresql_url(self):
        """Test that postgresql:// URLs are preserved"""
        from app.config import _normalized_database_url
        
        postgresql_url = 'postgresql://user:pass@localhost:5432/db'
        result = _normalized_database_url(postgresql_url)
        
        assert result == postgresql_url
    
    def test_default_url_when_not_set(self):
        """Test default URL is returned when DATABASE_URL not set"""
        old_db_url = os.environ.pop('DATABASE_URL', None)
        
        try:
            from app.config import _normalized_database_url
            default = 'sqlite:///app.db'
            result = _normalized_database_url(default)
            
            assert result == default
        finally:
            if old_db_url:
                os.environ['DATABASE_URL'] = old_db_url


class TestEnvironmentVariables:
    """Test environment variable handling"""
    
    def test_mail_port_conversion_to_int(self):
        """Test MAIL_PORT is converted to integer"""
        from app.config import Config
        
        config = Config()
        assert isinstance(config.MAIL_PORT, int)
    
    def test_mail_use_tls_string_conversion(self):
        """Test MAIL_USE_TLS string is converted to boolean"""
        os.environ['MAIL_USE_TLS'] = 'True'
        
        from app.config import Config
        config = Config()
        
        assert isinstance(config.MAIL_USE_TLS, bool)


class TestConfigurationDefaults:
    """Test configuration default values"""
    
    def test_default_session_timeout(self):
        """Test default session timeout is set"""
        from app.config import Config
        
        config = Config()
        assert hasattr(config, 'PERMANENT_SESSION_LIFETIME')
    
    def test_default_mail_server(self):
        """Test default mail server is configured"""
        from app.config import Config
        
        config = Config()
        assert config.MAIL_SERVER is not None


class TestJSONConfiguration:
    """Test JSON-related configuration"""
    
    def test_json_sort_keys_disabled(self):
        """Test JSON_SORT_KEYS is False for better readability"""
        from app.config import Config
        
        config = Config()
        assert config.JSON_SORT_KEYS is False


class TestSQLAlchemyConfiguration:
    """Test SQLAlchemy configuration"""
    
    def test_track_modifications_disabled(self):
        """Test SQLAlchemy tracking modifications is disabled"""
        from app.config import Config
        
        config = Config()
        assert config.SQLALCHEMY_TRACK_MODIFICATIONS is False
    
    def test_query_recording_enabled(self):
        """Test SQLAlchemy query recording is enabled for debugging"""
        from app.config import Config
        
        config = Config()
        assert config.SQLALCHEMY_RECORD_QUERIES is True
