# Testing & Deployment Guide

This guide covers how to run tests locally, set up the CI/CD pipeline, and deploy the application.

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend tests)
- PostgreSQL 15 (for production)
- Docker & Docker Compose (for containerized deployment)

## Backend Testing (Python/Pytest)

### Setup

1. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r config/requirements.txt
   pip install -r config/requirements-dev.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

### Running Tests

**Run all tests:**
```bash
pytest
```

**Run tests with coverage:**
```bash
pytest --cov=. --cov-report=html --cov-report=xml
```

**Run specific test file:**
```bash
pytest tests/test_backend_core.py -v
```

**Run tests matching pattern:**
```bash
pytest -k "test_health" -v
```

**Run with markers:**
```bash
pytest -m "unit" -v  # Run only unit tests
pytest -m "security" -v  # Run only security tests
```

### Test Organization

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures and configuration
├── test_backend_core.py     # Core functionality tests
├── test_api_endpoints.py    # API endpoint tests
└── test_utils.py            # Utility function tests
```

## Frontend Testing (JavaScript/Jest)

### Setup

1. **Install Node dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Install development dependencies:**
   ```bash
   npm install --save-dev
   ```

### Running Tests

**Run all tests:**
```bash
npm test
```

**Run tests in watch mode:**
```bash
npm run test:watch
```

**Run tests with coverage:**
```bash
npm run test:coverage
```

**Run specific test file:**
```bash
npm test -- api.test.js
```

### Test Organization

```
frontend/static/tests/
├── setup.js           # Jest setup and global mocks
├── api.test.js        # API service module tests
├── auth.test.js       # Authentication tests
└── storage.test.js    # Storage functionality tests
```

## Code Quality

### Python Code Quality

**Run all linters:**
```bash
# Format with black
black .

# Check import order
isort .

# Lint with flake8
flake8 app.py backend scripts --max-line-length=120

# Type checking with mypy
mypy app.py backend
```

### Frontend Code Quality

**Run ESLint:**
```bash
cd frontend
npm run lint
npm run lint:fix
```

## GitHub Actions CI/CD Pipeline

### Workflow Steps

1. **Lint** - Code quality checks (Python)
   - flake8 for style
   - black for formatting
   - isort for imports

2. **Security** - Vulnerability scanning
   - Trivy filesystem scan
   - Upload to GitHub Security

3. **Test** - Python unit tests
   - pytest with coverage
   - PostgreSQL integration tests
   - Coverage report to Codecov

4. **Test Frontend** - JavaScript unit tests
   - Jest test suite
   - Node.js 18.x and 20.x
   - Coverage report

5. **Build** - Docker image build (main branch only)
   - Build optimized image
   - Push to Docker Hub
   - Cache layers for speed

6. **Deploy** - Production deployment (main branch only)
   - Custom deployment script
   - Production environment

### Triggering Workflow

- **On push to main/develop branches**
- **On pull requests to main**

### GitHub Secrets Required

Add these secrets in GitHub Settings → Secrets:

```
DOCKER_USERNAME      # Docker Hub username
DOCKER_PASSWORD      # Docker Hub token/password
```

## Local Testing with Docker

### Run with Docker Compose

```bash
# Build and start services
docker-compose -f infra/docker-compose.yml up --build

# Run tests in container
docker-compose -f infra/docker-compose.yml exec app pytest -v

# Stop services
docker-compose -f infra/docker-compose.yml down
```

### Environment Variables

The `.env` file controls:
- Database connection
- Email configuration
- OAuth credentials
- API keys

**Never commit `.env` to version control!** Use `.env.example` as a template.

## Database Setup

### PostgreSQL (Production)

```bash
# Create database
createdb restaurant_ai

# Initialize schema
psql restaurant_ai < backend/database/setup_postgresql.sql

# Run migrations (if using Alembic)
alembic upgrade head
```

### SQLite (Development)

Database is auto-created at `restaurant_ai.db` on first run.

## Deployment

### Docker Build

```bash
# Build image
docker build -t restaurant-ai:latest .

# Run container
docker run -p 5000:5000 --env-file .env restaurant-ai:latest
```

### Docker Compose (Full Stack)

```bash
# Start all services
docker-compose -f infra/docker-compose.yml up -d

# View logs
docker-compose -f infra/docker-compose.yml logs -f

# Stop services
docker-compose -f infra/docker-compose.yml down

# Remove volumes (cleanup)
docker-compose -f infra/docker-compose.yml down -v
```

### Kubernetes Deployment

```bash
# Apply deployment
kubectl apply -f infra/k8s-deployment.yaml

# View status
kubectl get deployments
kubectl describe deployment restaurant-ai

# Scale deployment
kubectl scale deployment restaurant-ai --replicas=3
```

## Coverage Goals

- **Backend**: 50% minimum
- **Frontend**: 50% minimum
- Increase over time as features stabilize

## Troubleshooting

### Tests Fail Locally but Pass in CI

- Check Python version matches (should be 3.11)
- Ensure all dependencies installed: `pip install -r config/requirements.txt`
- Clear pytest cache: `pytest --cache-clear`
- Check DATABASE_URL environment variable

### Docker Build Fails

- Ensure Docker Desktop is running
- Check disk space: `docker system df`
- Clear cache: `docker system prune`
- Rebuild without cache: `docker build --no-cache .`

### Coverage Report Missing

- Install coverage: `pip install pytest-cov`
- Run: `pytest --cov=. --cov-report=html`
- Open: `htmlcov/index.html`

## Performance Testing

### Load Testing with Locust

```bash
# Install locust (included in requirements-dev.txt)
pip install locust

# Run load tests
locust -f scripts/locustfile.py --host http://localhost:5000
```

## Security Testing

### Bandit (Security Linting)

```bash
pip install bandit
bandit -r app backend scripts -f json -o bandit-report.json
```

### Dependency Vulnerability Check

```bash
pip install safety
safety check
```

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)
- [Flask Testing](https://flask.palletsprojects.com/testing/)
- [Docker Documentation](https://docs.docker.com/)
- [GitHub Actions](https://docs.github.com/en/actions)
