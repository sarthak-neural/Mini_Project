"""
Comprehensive test suite for Restaurant Inventory AI
Tests cover authentication, user management, dashboard, forecasts, and alerts
"""

import unittest
import json
import os
from datetime import datetime, timedelta
from app import app, db, User, Location, SalesRecord, AlertPreference, Forecast
from models import IngredientMaster
import tempfile


class RestaurantInventoryTestCase(unittest.TestCase):
    """Base test case with setup and teardown"""

    def setUp(self):
        """Set up test client and database"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up test database"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
        
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def register_user(self, email, password, first_name="Test", last_name="User", 
                     restaurant_name="Test Restaurant", role="manager"):
        """Helper to register a test user"""
        return self.client.post('/signup', data={
            'email': email,
            'password': password,
            'first_name': first_name,
            'last_name': last_name,
            'restaurant_name': restaurant_name,
            'role': role,
            'country': 'US',
            'city': 'New York'
        }, follow_redirects=True)
    
    def login_user(self, email, password, role="manager"):
        """Helper to login a test user"""
        return self.client.post('/login', data={
            'email': email,
            'password': password,
            'role': role
        }, follow_redirects=True)
    
    def logout_user(self):
        """Helper to logout"""
        return self.client.get('/logout', follow_redirects=True)


class AuthenticationTests(RestaurantInventoryTestCase):
    """Test authentication and user creation"""
    
    def test_landing_page(self):
        """Test landing page is accessible"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Restaurant Inventory AI', response.data)
    
    def test_user_signup(self):
        """Test user registration"""
        response = self.register_user('test@example.com', 'TestPassword123!')
        self.assertIn(b'Dashboard', response.data)
    
    def test_duplicate_email_signup(self):
        """Test that duplicate emails are rejected"""
        self.register_user('test@example.com', 'TestPassword123!')
        response = self.register_user('test@example.com', 'DifferentPassword123!')
        self.assertIn(b'Email already registered', response.data)
    
    def test_user_login(self):
        """Test user login"""
        self.register_user('test@example.com', 'TestPassword123!')
        response = self.login_user('test@example.com', 'TestPassword123!')
        self.assertIn(b'Dashboard', response.data)
    
    def test_invalid_login(self):
        """Test login with wrong password"""
        self.register_user('test@example.com', 'TestPassword123!')
        response = self.login_user('test@example.com', 'WrongPassword!')
        self.assertIn(b'Invalid credentials', response.data)
    
    def test_user_logout(self):
        """Test user logout"""
        self.register_user('test@example.com', 'TestPassword123!')
        self.login_user('test@example.com', 'TestPassword123!')
        response = self.logout_user()
        self.assertEqual(response.status_code, 200)
    
    def test_login_required_decorator(self):
        """Test that protected routes require login"""
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 302)  # Redirect to login


class UserProfileTests(RestaurantInventoryTestCase):
    """Test user profile and settings"""
    
    def setUp(self):
        super().setUp()
        self.register_user('test@example.com', 'TestPassword123!')
        self.login_user('test@example.com', 'TestPassword123!')
    
    def test_settings_page_accessible(self):
        """Test settings page is accessible after login"""
        response = self.client.get('/settings')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Account Settings', response.data)
    
    def test_get_user_profile(self):
        """Test retrieving user profile via API"""
        response = self.client.get('/api/user/profile')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['email'], 'test@example.com')
    
    def test_update_user_profile(self):
        """Test updating user profile"""
        response = self.client.post('/api/user/profile', 
            data=json.dumps({
                'first_name': 'Updated',
                'last_name': 'Name',
                'restaurant_name': 'New Restaurant'
            }),
            content_type='application/json')
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify update
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            self.assertEqual(user.first_name, 'Updated')
            self.assertEqual(user.last_name, 'Name')
            self.assertEqual(user.restaurant_name, 'New Restaurant')
    
    def test_change_password(self):
        """Test password change"""
        response = self.client.post('/api/user/change-password',
            data=json.dumps({
                'current_password': 'TestPassword123!',
                'new_password': 'NewPassword456!'
            }),
            content_type='application/json')
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify old password doesn't work
        self.logout_user()
        response = self.login_user('test@example.com', 'TestPassword123!')
        self.assertIn(b'Invalid credentials', response.data)
        
        # Verify new password works
        response = self.login_user('test@example.com', 'NewPassword456!')
        self.assertIn(b'Dashboard', response.data)
    
    def test_invalid_password_change(self):
        """Test that weak passwords are rejected"""
        response = self.client.post('/api/user/change-password',
            data=json.dumps({
                'current_password': 'TestPassword123!',
                'new_password': 'weak'
            }),
            content_type='application/json')
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])


class PasswordRecoveryTests(RestaurantInventoryTestCase):
    """Test password recovery functionality"""
    
    def setUp(self):
        super().setUp()
        self.register_user('test@example.com', 'TestPassword123!')
    
    def test_password_recovery_page(self):
        """Test password recovery page is accessible"""
        response = self.client.get('/password-recovery')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Password Recovery', response.data)
    
    def test_request_recovery_code(self):
        """Test requesting recovery code"""
        response = self.client.post('/api/auth/request-recovery-code',
            data=json.dumps({'email': 'test@example.com'}),
            content_type='application/json')
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_recovery_code_not_found(self):
        """Test recovery code request for non-existent user"""
        response = self.client.post('/api/auth/request-recovery-code',
            data=json.dumps({'email': 'nonexistent@example.com'}),
            content_type='application/json')
        
        # Should return success but not actually send (security)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_verify_invalid_recovery_code(self):
        """Test verification with invalid code"""
        response = self.client.post('/api/auth/verify-recovery-code',
            data=json.dumps({
                'email': 'test@example.com',
                'code': '000000'
            }),
            content_type='application/json')
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])


class DashboardTests(RestaurantInventoryTestCase):
    """Test dashboard and statistics"""
    
    def setUp(self):
        super().setUp()
        self.register_user('test@example.com', 'TestPassword123!')
        self.login_user('test@example.com', 'TestPassword123!')
    
    def test_dashboard_accessible(self):
        """Test dashboard page is accessible"""
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Inventory Dashboard', response.data)
    
    def test_dashboard_stats_api(self):
        """Test dashboard statistics API"""
        response = self.client.get('/api/dashboard-stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('stats', data)
        self.assertIn('total_ingredients', data['stats'])
        self.assertIn('total_sales', data['stats'])
    
    def test_ingredients_api(self):
        """Test ingredients API"""
        response = self.client.get('/api/ingredients')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('ingredients', data)


class SalesRecordTests(RestaurantInventoryTestCase):
    """Test sales record functionality"""
    
    def setUp(self):
        super().setUp()
        self.register_user('test@example.com', 'TestPassword123!')
        self.login_user('test@example.com', 'TestPassword123!')
    
    def test_add_sale(self):
        """Test adding a sales record"""
        response = self.client.post('/api/add-sale',
            data=json.dumps({
                'ingredient': 'Tomato',
                'quantity': 10.5,
                'date': datetime.now().strftime('%Y-%m-%d')
            }),
            content_type='application/json')
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify record was created
        with app.app_context():
            sale = SalesRecord.query.filter_by(ingredient='Tomato').first()
            self.assertIsNotNone(sale)
            self.assertEqual(sale.quantity_sold, 10.5)
    
    def test_upload_csv(self):
        """Test CSV upload"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('date,ingredient,quantity_sold\n')
            f.write('2024-01-01,Tomato,10\n')
            f.write('2024-01-02,Onion,5\n')
            f.flush()
            
            with open(f.name, 'rb') as csv_file:
                response = self.client.post('/api/upload-csv',
                    data={'file': (csv_file, 'test.csv')})
            
            self.assertEqual(response.status_code, 200)
        
        os.unlink(f.name)


class AlertTests(RestaurantInventoryTestCase):
    """Test alert preferences and notifications"""
    
    def setUp(self):
        super().setUp()
        self.register_user('test@example.com', 'TestPassword123!')
        self.login_user('test@example.com', 'TestPassword123!')
    
    def test_get_alert_preferences(self):
        """Test getting alert preferences"""
        response = self.client.get('/api/alerts/preferences')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_update_alert_preferences(self):
        """Test updating alert preferences"""
        response = self.client.post('/api/alerts/preferences',
            data=json.dumps({
                'email_address': 'alerts@example.com',
                'email_enabled': True,
                'threshold_percentage': 25
            }),
            content_type='application/json')
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify update
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            prefs = user.alert_preferences
            self.assertEqual(prefs.email_address, 'alerts@example.com')
            self.assertTrue(prefs.email_enabled)
            self.assertEqual(prefs.threshold_percentage, 25)
    
    def test_check_stock_alert(self):
        """Test low stock alert check"""
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            prefs = user.alert_preferences
            if not prefs:
                prefs = AlertPreference(user_id=user.id)
                db.session.add(prefs)
                db.session.commit()
        
        response = self.client.post('/api/alerts/check-stock',
            data=json.dumps({
                'ingredient': 'Tomato',
                'current_stock': 5,
                'reorder_point': 20
            }),
            content_type='application/json')
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])


class LocationTests(RestaurantInventoryTestCase):
    """Test location and unit settings"""
    
    def setUp(self):
        super().setUp()
        self.register_user('test@example.com', 'TestPassword123!')
        self.login_user('test@example.com', 'TestPassword123!')
    
    def test_get_user_location(self):
        """Test getting user location"""
        response = self.client.get('/api/user/location')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('location', data)
        self.assertIn('units', data)
    
    def test_update_location(self):
        """Test updating location"""
        response = self.client.post('/api/location/country',
            data=json.dumps({
                'country': 'CA',
                'city': 'Toronto'
            }),
            content_type='application/json')
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify units changed
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            units = user.location.get_units()
            self.assertEqual(units['weight'], 'kg')
            self.assertEqual(units['currency'], 'CAD')
    
    def test_unit_conversion(self):
        """Test unit conversion API"""
        response = self.client.post('/api/convert-units',
            data=json.dumps({
                'value': 1,
                'from_unit': 'lbs',
                'to_unit': 'kg'
            }),
            content_type='application/json')
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertAlmostEqual(data['result'], 0.453592, places=5)


class ForecastTests(RestaurantInventoryTestCase):
    """Test forecast functionality"""
    
    def setUp(self):
        super().setUp()
        self.register_user('test@example.com', 'TestPassword123!')
        self.login_user('test@example.com', 'TestPassword123!')
        
        # Add some sample data
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            for i in range(30):
                date = datetime.now() - timedelta(days=30-i)
                sale = SalesRecord(
                    user_id=user.id,
                    ingredient='Tomato',
                    quantity_sold=10 + i % 5,
                    sale_date=date.date()
                )
                db.session.add(sale)
            db.session.commit()
    
    def test_forecast_page(self):
        """Test forecast page is accessible"""
        response = self.client.get('/forecast')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Forecast', response.data)
    
    def test_forecast_api(self):
        """Test forecast API"""
        response = self.client.post('/api/forecast',
            data=json.dumps({
                'ingredient': 'Tomato',
                'days_ahead': 7
            }),
            content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])


class ErrorHandlingTests(RestaurantInventoryTestCase):
    """Test error handling"""
    
    def test_404_error(self):
        """Test 404 error handling"""
        response = self.client.get('/nonexistent-page')
        self.assertEqual(response.status_code, 404)
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        response = self.client.post('/api/add-sale',
            data=json.dumps({}),
            content_type='application/json')
        
        # Should return 400 or error response
        self.assertIn(response.status_code, [400, 422, 500])


class PerformanceTests(RestaurantInventoryTestCase):
    """Test performance and optimization"""
    
    def setUp(self):
        super().setUp()
        self.register_user('test@example.com', 'TestPassword123!')
        self.login_user('test@example.com', 'TestPassword123!')
    
    def test_dashboard_response_time(self):
        """Test dashboard response time"""
        import time
        start = time.time()
        response = self.client.get('/api/dashboard-stats')
        elapsed = time.time() - start
        
        # Should respond in less than 1 second
        self.assertLess(elapsed, 1.0)
        self.assertEqual(response.status_code, 200)


class SecurityTests(RestaurantInventoryTestCase):
    """Test security features"""
    
    def test_password_hashing(self):
        """Test that passwords are hashed"""
        with app.app_context():
            self.register_user('test@example.com', 'TestPassword123!')
            user = User.query.filter_by(email='test@example.com').first()
            # Password should be hashed, not plain text
            self.assertNotEqual(user.password_hash, 'TestPassword123!')
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        response = self.client.post('/login', data={
            'email': "'; DROP TABLE users; --",
            'password': 'anything',
            'role': 'manager'
        })
        # Should not crash or drop tables
        self.assertEqual(response.status_code, 200)
    
    def test_csrf_protection_enabled(self):
        """Test CSRF protection"""
        # In production, CSRF should be enabled
        # This test just verifies the app has CSRF handling set up
        self.assertFalse(app.config.get('WTF_CSRF_ENABLED', True) is False)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)
