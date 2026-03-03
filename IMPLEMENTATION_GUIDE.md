# Implementation Guide - New Features

This guide helps developers understand and implement the new features added to Restaurant Inventory AI.

## Quick Start

### 1. Install Dependencies

```bash
# Core dependencies already in requirements.txt
pip install -r requirements.txt

# Development/testing dependencies
pip install -r requirements-dev.txt
```

### 2. Initialize Database

```bash
python init_db.py
```

### 3. Run Application

```bash
python app.py
```

### 4. Run Tests

```bash
python -m pytest tests.py -v
```

## Feature: Enhanced Dashboard Visualizations

### Usage

The dashboard now supports advanced charts through `advanced-charts.js` module:

```javascript
// Render inventory level chart
advancedCharts.renderInventoryLevelChart('containerId', {
    total_capacity: 1000,
    current_stock: 750,
    safety_stock: 300,
    reorder_point: 500
});

// Render seasonal trend
advancedCharts.renderSeasonalTrendChart('containerId', {
    labels: ['Week 1', 'Week 2', ...],
    actual: [100, 120, ...],
    seasonal_avg: [110, 115, ...],
    trend: [105, 117, ...]
});

// Render cost analysis
advancedCharts.renderCostAnalysisChart('containerId', {
    labels: ['Item1', 'Item2', ...],
    current_cost: [50, 45, ...],
    average_cost: [48, 48, ...],
    target_cost: [45, 40, ...]
});
```

### Extending

To add new chart types:

1. Add method to `advancedCharts` object
2. Create Chart.js configuration
3. Update dashboard to call method
4. Add CSS styling if needed

Example:

```javascript
advancedCharts.renderNewChart = function(containerId, data) {
    const ctx = document.getElementById(containerId);
    if (!ctx) return;
    
    // Destroy existing if any
    if (this.newChart) {
        this.newChart.destroy();
    }
    
    // Create new chart
    this.newChart = new Chart(ctx, {
        type: 'type',
        data: { /* ... */ },
        options: { /* ... */ }
    });
};
```

## Feature: User Settings Management

### Routes

- **GET `/settings`** - Settings page (requires login)
- **GET/POST `/api/user/profile`** - Profile management
- **POST `/api/user/change-password`** - Password change
- **POST `/api/user/delete-account`** - Account deletion

### JavaScript Integration

```javascript
// Load user profile
loadUserProfile();

// Update profile
fetch('/api/user/profile', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        first_name: 'John',
        last_name: 'Doe',
        restaurant_name: 'My Restaurant'
    })
});

// Change password
fetch('/api/user/change-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        current_password: 'OldPassword123!',
        new_password: 'NewPassword456!'
    })
});
```

### Adding New Settings Sections

1. Add menu item in `settings.html`:
```html
<li class="settings-menu-item">
  <a href="#new-setting" class="settings-menu-link" 
     onclick="switchPanel('new-setting')">
    <i class="fas fa-icon"></i> New Setting
  </a>
</li>
```

2. Add panel in HTML:
```html
<div id="new-setting-panel" class="settings-panel">
  <div class="settings-section">
    <h2><i class="fas fa-icon"></i> New Setting</h2>
    <!-- Form content -->
  </div>
</div>
```

3. Add handler in `settings.js`:
```javascript
document.getElementById('new-setting-form').addEventListener('submit', 
    async function(e) {
        e.preventDefault();
        // Handle submission
    }
);
```

## Feature: Password Recovery

### Routes

- **GET `/password-recovery`** - Recovery page (public)
- **POST `/api/auth/request-recovery-code`** - Request code
- **POST `/api/auth/verify-recovery-code`** - Verify code
- **POST `/api/auth/reset-password`** - Reset password

### Flow

```
User Email → Generate Token → Send Email → Verify Code → Reset Password
```

### Email Configuration

In `.env`:

```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@restaurantai.com
```

### Customizing Recovery Email

In `app.py`, customize the message:

```python
msg = Message(
    subject="Your Recovery Code",
    recipients=[email],
    body=f"""
Dear {user.get_full_name()},

Your recovery code is: {token}

This code expires in 1 hour.
...
    """
)
```

### Rate Limiting

Configured in `app.py`:

```python
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Custom limits on recovery endpoints
@limiter.limit("3 per hour")
def request_recovery_code():
    ...
```

Modify limits as needed for your use case.

## Feature: Comprehensive Testing

### Test Structure

```
tests.py
├── RestaurantInventoryTestCase (base class)
├── AuthenticationTests
├── UserProfileTests
├── PasswordRecoveryTests
├── DashboardTests
├── SalesRecordTests
├── AlertTests
├── LocationTests
├── ForecastTests
├── ErrorHandlingTests
├── PerformanceTests
└── SecurityTests
```

### Writing New Tests

```python
class MyNewTests(RestaurantInventoryTestCase):
    def setUp(self):
        super().setUp()
        # Set up test data
        self.register_user('test@example.com', 'TestPassword123!')
    
    def test_my_feature(self):
        # Test implementation
        response = self.client.get('/my-endpoint')
        self.assertEqual(response.status_code, 200)
        
        # Verify database
        with app.app_context():
            obj = MyModel.query.first()
            self.assertIsNotNone(obj)
```

### Running Tests

```bash
# All tests
python -m pytest tests.py -v

# Specific test class
python -m pytest tests.py::MyNewTests -v

# Specific test
python -m pytest tests.py::MyNewTests::test_my_feature -v

# With coverage
coverage run -m pytest tests.py
coverage report
coverage html

# Watch mode (if pytest-watch installed)
ptw tests.py
```

### CI/CD Integration

GitHub Actions example:

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest tests.py --cov=. --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Code Organization

### New Files

```
project/
├── templates/
│   ├── settings.html          # User settings page
│   └── password_recovery.html # Password recovery page
├── static/
│   ├── advanced-charts.js     # Advanced chart module
│   ├── settings.js            # Settings page JS
│   └── password-recovery.js   # Recovery page JS
├── tests.py                   # Test suite
├── pytest.ini                 # Pytest config
├── TESTING_COMPREHENSIVE.md   # Testing guide
├── ENHANCEMENT_SUMMARY.md     # Enhancement summary
└── IMPLEMENTATION_GUIDE.md    # This file
```

### Updated Files

```
app.py
├── New routes:
│   ├── /settings
│   ├── /password-recovery
│   ├── /api/user/profile
│   ├── /api/user/change-password
│   ├── /api/user/delete-account
│   ├── /api/auth/request-recovery-code
│   ├── /api/auth/verify-recovery-code
│   └── /api/auth/reset-password
├── New imports:
│   ├── flask_limiter
│   └── recovery token functions
└── New functions:
    ├── generate_recovery_token()
    ├── store_recovery_token()
    └── verify_recovery_token()

templates/dashboard.html, index.html, login.html
├── Updated nav links to /settings
└── Updated password recovery link
```

## Debugging

### Common Issues

**1. Settings page not loading**
- Check if user is logged in
- Verify session['user'] is set
- Check browser console for JS errors

**2. Email not sending for password recovery**
- Verify email config in `.env`
- Check MAIL_USERNAME and MAIL_PASSWORD
- Look at app logs for email errors
- Test with simple script:
```python
from flask_mail import Mail, Message
mail = Mail(app)
msg = Message('Test', recipients=['test@example.com'])
mail.send(msg)
```

**3. Tests failing**
- Check database is clean
- Verify all fixtures are in setUp()
- Run individual test to isolate issue
- Use `-v -s` flags for debug output

### Debug Mode

Enable debug logging:

```python
# In app.py
import logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)
```

View application logs:

```bash
# Python logging
python -m pdb app.py  # Step through code

# Check logs files if configured
tail -f /var/log/restaurant_inventory.log
```

## Performance Optimization

### Database Queries

Use eager loading for relationships:

```python
user = User.query.options(
    joinedload('location'),
    joinedload('alert_preferences')
).first()
```

### Caching

Add caching for expensive operations:

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/dashboard-stats')
@cache.cached(timeout=300)
def dashboard_stats():
    # Cached for 5 minutes
    pass
```

### Frontend Performance

- Minify CSS/JS in production
- Use CDN for libraries
- Lazy load images
- Compress chart data

## Security Considerations

### Input Validation

Always validate user input:

```python
from wtforms import validators

if not email or '@' not in email:
    return jsonify({"error": "Invalid email"}), 400
```

### SQL Injection Prevention

Use parameterized queries (SQLAlchemy does this):

```python
# Safe
user = User.query.filter_by(email=email).first()

# Unsafe - DON'T DO THIS
user = User.query.filter(f"email='{email}'").first()
```

### CSRF Protection

Enable CSRF in production:

```python
app.config['WTF_CSRF_ENABLED'] = True
csrf = CSRFProtect(app)
```

### Password Hashing

Always hash passwords:

```python
user.set_password(password)  # Uses pbkdf2:sha256
```

## Monitoring

### Key Metrics

- Response times (target: < 500ms)
- Error rates (target: < 0.1%)
- Database query times
- Email delivery success
- Test coverage (target: > 80%)

### Health Checks

```bash
# Dashboard stats API
curl http://localhost:5000/api/dashboard-stats

# Health endpoint
curl http://localhost:5000/health

# Readiness
curl http://localhost:5000/health/ready
```

## Next Doors

1. Implement two-factor authentication
2. Add session management
3. Create mobile app
4. Add advanced analytics
5. Implement audit logging
6. Add API documentation (Swagger/OpenAPI)
7. Create admin dashboard
8. Add batch import/export

## Support & Resources

- API Documentation: See docstrings in app.py
- Testing Guide: See TESTING_COMPREHENSIVE.md
- Feature Summary: See ENHANCEMENT_SUMMARY.md
- Flask Docs: https://flask.palletsprojects.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Chart.js: https://www.chartjs.org/

## Contributing

When adding new features:

1. Write tests first (TDD)
2. Implement feature
3. Update documentation
4. Run full test suite
5. Check code for security issues
6. Verify performance
7. Submit for review

## Contact

For questions or issues, contact the development team.
