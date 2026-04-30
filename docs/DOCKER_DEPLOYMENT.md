# Docker & Deployment Configuration

This document describes the Docker setup and deployment options for the Restaurant Inventory AI application.

## Overview

The application uses a multi-stage Docker build for optimized production images and provides multiple deployment scenarios:

- **Local Development**: docker-compose.dev.yml with hot reload
- **Production**: docker-compose.yml with full stack (PostgreSQL, Redis, Nginx)
- **Kubernetes**: k8s-deployment.yaml for container orchestration

## Docker Architecture

### Multi-Stage Build

The Dockerfile uses a two-stage build process:

1. **Builder Stage**: Compiles dependencies in a full development environment
2. **Runtime Stage**: Minimal production image with only runtime dependencies

**Benefits:**
- Smaller final image size (~400MB vs ~800MB)
- Faster pulls and deployments
- Reduced security surface area
- Better layer caching

### Image Optimization

The production Dockerfile includes:
- Security: Non-root user (appuser:1000)
- Health checks: Liveness probe via `/health` endpoint
- Signals: Proper SIGTERM handling in gunicorn
- Caching: Optimized layer order
- Minimal base: Python 3.11-slim as base image

## Files Structure

```
infra/
├── Dockerfile              # Production-ready multi-stage build
├── docker-compose.yml      # Production stack
├── docker-compose.dev.yml  # Development stack
├── nginx.conf              # Reverse proxy configuration
├── ssl/                    # SSL certificates (if using HTTPS)
└── k8s-deployment.yaml     # Kubernetes deployment
```

## Development Setup

### Quick Start with Docker Compose

```bash
# Start development environment
cd infra
docker-compose -f docker-compose.dev.yml up

# In another terminal
docker-compose -f docker-compose.dev.yml exec app flask init-db

# View logs
docker-compose -f docker-compose.dev.yml logs -f app

# Stop services
docker-compose -f docker-compose.dev.yml down
```

### Development Environment Features

- **Hot reload**: Changes reflected immediately
- **SQLite database**: Pre-configured, no setup needed
- **Debug mode**: Flask debug server with auto-restart
- **Volume mounts**: Live code editing
- **Simplified networking**: Single network for all services

### Running Tests in Development

```bash
# Run pytest
docker-compose -f docker-compose.dev.yml exec app pytest -v

# Run with coverage
docker-compose -f docker-compose.dev.yml exec app pytest --cov=. --cov-report=html

# Run frontend tests
docker-compose -f docker-compose.dev.yml exec app npm test
```

## Production Setup

### Pre-Deployment Checklist

- [ ] `.env` configured with production values
- [ ] `SECRET_KEY` is a strong, random 64+ character string
- [ ] `DATABASE_URL` points to PostgreSQL (not SQLite)
- [ ] Email credentials configured
- [ ] SSL certificates in place (if using HTTPS)
- [ ] Docker Hub credentials configured (for CI/CD)

### Building for Production

```bash
# Build image locally
docker build -t restaurant-ai:latest .

# Build with specific tag
docker build -t restaurant-ai:v1.0.0 .

# Build without cache (clean rebuild)
docker build --no-cache -t restaurant-ai:latest .

# Build for specific platform (for ARM, Intel, etc.)
docker buildx build --platform linux/amd64,linux/arm64 -t restaurant-ai:latest .
```

### Starting Production Stack

```bash
cd infra

# Create .env from .env.example
cp ../.env.example .env
# Edit .env with production values

# Start services in background
docker-compose -f docker-compose.yml up -d

# View status
docker-compose -f docker-compose.yml ps

# View logs
docker-compose -f docker-compose.yml logs -f app

# Monitor specific service
docker-compose -f docker-compose.yml logs -f --tail=100 postgres

# Stop services
docker-compose -f docker-compose.yml stop

# Remove containers
docker-compose -f docker-compose.yml down

# Remove containers and volumes (WARNING: deletes data)
docker-compose -f docker-compose.yml down -v
```

### Production Stack Components

#### PostgreSQL Database
- Image: postgres:15-alpine
- Credentials: Via environment variables
- Data: Persistent volume (`postgres_data`)
- Health checks: Built-in readiness probe

#### Redis Cache
- Image: redis:7-alpine
- Port: 6379 (internal only)
- Data: Persistent volume (`redis_data`)
- Used for: Session caching, rate limiting

#### Flask Application
- Built from Dockerfile
- Runs gunicorn with 4 workers
- Health checks every 30 seconds
- Restart policy: unless-stopped
- Logs: Mapped to local `logs/` directory

#### Nginx Reverse Proxy
- Image: nginx:alpine
- Ports: 80 (HTTP), 443 (HTTPS with SSL)
- Static files: 30-day browser cache
- Compression: gzip for text content
- Security headers: XSS, CSP, X-Frame-Options

### Environment Variables

Create `.env` in `infra/` directory:

```bash
# Database
DB_USER=restaurant_user
DB_PASSWORD=very-secure-password-here
DB_NAME=restaurant_ai
DB_PORT=5432

# Application
APP_PORT=5000
SECRET_KEY=your-secret-key-min-64-chars-xxxxxxxx
FLASK_ENV=production
DEBUG=False

# Email (Gmail example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Twilio (SMS OTP)
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# Redis
REDIS_PORT=6379

# Third-party APIs
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx
```

## Kubernetes Deployment

### Prerequisites

- kubectl configured
- Kubernetes cluster (EKS, GKE, AKS, or local)
- Container registry (ECR, GCR, ACR, or Docker Hub)

### Deployment Steps

```bash
# Build and push image to registry
docker build -t <registry>/restaurant-ai:latest .
docker push <registry>/restaurant-ai:latest

# Create namespace
kubectl create namespace restaurant-ai

# Create secrets from .env
kubectl create secret generic app-secrets \
  --from-env-file=.env \
  -n restaurant-ai

# Deploy application
kubectl apply -f infra/k8s-deployment.yaml -n restaurant-ai

# Check deployment status
kubectl get deployments -n restaurant-ai
kubectl describe deployment restaurant-ai -n restaurant-ai

# View pods
kubectl get pods -n restaurant-ai
kubectl logs -f deployment/restaurant-ai -n restaurant-ai

# Scale deployment
kubectl scale deployment restaurant-ai --replicas=3 -n restaurant-ai

# Update deployment (rolling restart)
kubectl rollout restart deployment/restaurant-ai -n restaurant-ai
```

### Kubernetes Configuration

The `k8s-deployment.yaml` includes:
- **Deployment**: 2 replicas with rolling updates
- **Service**: LoadBalancer for external access
- **ConfigMap**: Non-sensitive configuration
- **PersistentVolume**: For PostgreSQL and logs
- **Resource limits**: CPU and memory constraints
- **Liveness probe**: Health check at `/health`
- **Readiness probe**: Readiness check at `/health/ready`

## Monitoring & Logging

### View Logs

```bash
# Docker Compose
docker-compose -f docker-compose.yml logs -f app

# Kubernetes
kubectl logs -f deployment/restaurant-ai -n restaurant-ai
kubectl logs -f pod/restaurant-ai-xxxxx -n restaurant-ai

# Stream last 100 lines
docker-compose -f docker-compose.yml logs -f --tail=100 app
```

### Health Checks

```bash
# Basic health check
curl http://localhost:5000/health

# Detailed readiness check
curl http://localhost:5000/health/ready

# With database status
curl -s http://localhost:5000/health/ready | jq .
```

### Docker System Cleanup

```bash
# View disk usage
docker system df

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Full cleanup (WARNING: removes all unused resources)
docker system prune -a --volumes
```

## Troubleshooting

### Application fails to start

```bash
# Check logs
docker-compose -f docker-compose.yml logs app

# Common issues:
# 1. PORT already in use: Change APP_PORT in .env
# 2. DATABASE_URL invalid: Verify connection string
# 3. Secret key not set: Check SECRET_KEY in .env
```

### Database connection refused

```bash
# Verify PostgreSQL is running
docker-compose -f docker-compose.yml ps postgres

# Check database logs
docker-compose -f docker-compose.yml logs postgres

# Connect to database manually
psql postgresql://user:password@localhost/restaurant_ai
```

### High memory usage

```bash
# Check container stats
docker stats

# Limit memory
docker-compose -f docker-compose.yml exec app free -h

# Restart services to reset
docker-compose -f docker-compose.yml restart
```

### Volume mount issues (Windows)

```bash
# Ensure Docker Desktop is running
# Check file sharing settings in Docker Desktop preferences
# Try using VOLUME in Dockerfile instead of -v flag
```

## Performance Tuning

### Database Connection Pool

Edit `config/gunicorn.conf.py`:
```python
# Increase worker connections
workers = cpu_count() * 2 + 1
worker_class = 'gevent'
worker_connections = 1000
```

### Redis Caching

Ensure Redis is configured in `.env`:
```bash
REDIS_URL=redis://redis:6379/0
```

### Static File Serving

With Nginx in front:
- Static files: 30-day cache
- Gzip compression: On for text content
- Upstream: Load balanced across app instances

## Security Best Practices

1. **Never commit `.env`** - Use `.env.example` as template
2. **Use strong SECRET_KEY** - At least 64 random characters
3. **Update images regularly** - `docker pull` latest base images
4. **Use HTTPS** - Configure SSL certificates
5. **Network isolation** - Don't expose databases publicly
6. **Non-root user** - Always run as appuser, not root
7. **Health checks** - Enable for all services
8. **Resource limits** - Set memory and CPU constraints

## CI/CD Integration

GitHub Actions workflow (`.github/workflows/ci.yml`) automatically:

1. Builds Docker image
2. Runs security scanning
3. Pushes to Docker Hub (on main branch)
4. Tags with commit SHA and `latest`

Configure Docker Hub credentials in GitHub Secrets:
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Multi-stage Builds Best Practices](https://docs.docker.com/build/building/multi-stage/)
