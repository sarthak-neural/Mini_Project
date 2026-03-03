# Test Coverage Guide

This document provides guidance on running and understanding the comprehensive test suite for Restaurant Inventory AI.

## Overview

The test suite includes **25+ test cases** covering:

- **Authentication** (6 tests)
  - User registration
  - User login/logout
  - Invalid credentials
  - Login required protection

- **User Profile & Settings** (6 tests)
  - Profile retrieval and updates
  - Password changes
  - Password validation
  - Settings page access

- **Password Recovery** (4 tests)
  - Recovery page access
  - Recovery code requests
  - Code verification
  - Password reset

- **Dashboard** (3 tests)
  - Dashboard page access
  - Statistics API
  - Ingredient listing

- **Sales Records** (2 tests)
  - Adding sales
  - CSV uploads

- **Alerts** (3 tests)
  - Alert preferences
  - Preference updates
  - Stock alert checks

- **Location & Units** (3 tests)
  - Location retrieval
  - Location updates
  - Unit conversions

- **Forecasting** (2 tests)
  - Forecast page
  - Forecast API

- **Error Handling** (2 tests)
  - 404 errors
  - Missing fields

- **Performance** (1 test)
  - Response time verification

- **Security** (3 tests)
  - Password hashing
  - SQL injection prevention
  - CSRF protection

## Running Tests

### Prerequisites

```bash
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
python -m pytest tests.py -v
```

Or with unittest:

```bash
python tests.py
```

### Run Specific Test Class

```bash
python -m pytest tests.py::AuthenticationTests -v
```

### Run Specific Test

```bash
python -m pytest tests.py::AuthenticationTests::test_user_signup -v
```

### Generate Coverage Report

```bash
pip install coverage
coverage run -m pytest tests.py
coverage report
coverage html  # Generates HTML report in htmlcov/
```

## Test Results

Expected output when running full test suite:

```
test_add_sale (tests.SalesRecordTests) ... ok
test_alert_preferences (tests.AlertTests) ... ok
test_change_password (tests.UserProfileTests) ... ok
test_dashboard_accessible (tests.DashboardTests) ... ok
...
----------------------------------------------------------------------
Ran 25 tests in 2.345s

OK
```

## Key Test Scenarios

### Authentication Flow
1. User registers with valid credentials
2. User logs in with correct password
3. User receives error with invalid password
4. Protected routes redirect unauthenticated users

### User Settings Flow
1. User updates profile information
2. User changes password with validation
3. User updates location and units
4. Changes persist in database

### Password Recovery Flow
1. User requests recovery code
2. Recovery code is generated and stored
3. User verifies code
4. User resets password
5. Recovery token is cleaned up

### Dashboard Flow
1. Dashboard loads with user data
2. Statistics are calculated correctly
3. Charts render with proper data
4. Ingredient list populates

### Alert Flow
1. Alert preferences are stored
2. Email/SMS toggles work
3. Threshold updates apply
4. Stock checks trigger alerts

## Coverage Targets

- **Overall**: >80% code coverage
- **Critical paths**: 100% coverage
  - Authentication
  - Password management
  - User data operations

## Running Tests in CI/CD

Example GitHub Actions workflow:

```yaml
- name: Run tests
  run: |
    pip install -r requirements-dev.txt
    python -m pytest tests.py --cov=. --cov-report=xml
```

## Debugging Tests

### Run with Debug Output

```bash
python -m pytest tests.py -v -s
```

The `-s` flag shows print statements and debug output.

### Debug Single Test

```bash
python -m pdb tests.py SalesRecordTests.test_add_sale
```

### Check Database State During Test

Add this to test methods:

```python
def test_something(self):
    # ... test code ...
    with app.app_context():
        users = User.query.all()
        print(f"Users in DB: {users}")
```

## Test Database

Tests use SQLite in-memory database for speed and isolation:

- Each test gets fresh database
- No test data persists
- Tests run in parallel safely
- No cleanup needed between tests

## Mocking External Services

For email/SMS tests in production:

```python
from unittest.mock import patch

@patch('flask_mail.Mail.send')
def test_email_alert(self, mock_send):
    # Test without actually sending email
    mock_send.return_value = True
```

## Performance Benchmarks

Tests verify performance targets:

- Dashboard stats: < 1 second
- API responses: < 500ms
- Database queries: < 100ms

## Continuous Integration

Recommended setup:

1. Run tests on every push
2. Block merges if tests fail
3. Generate coverage report
4. Track coverage trends
5. Alert on performance regression

## Next Steps

- [ ] Add integration tests
- [ ] Add end-to-end tests
- [ ] Add load/stress tests
- [ ] Add security penetration tests
- [ ] Add accessibility tests

## Support

If tests fail:

1. Check error message
2. Review test code
3. Check fixture setup
4. Verify database state
5. Check for timing issues
