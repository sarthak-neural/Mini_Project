"""
Gunicorn production server configuration.

Defaults are tuned for small hosted instances (e.g., Render free/starter)
where ML dependencies make each worker memory-heavy.
"""
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
backlog = 2048

# Worker processes
# Use one worker by default to avoid OOM restarts with heavy ML imports.
workers = int(os.getenv('GUNICORN_WORKERS', '1'))
worker_class = 'sync'  # Use 'gevent' or 'eventlet' for async
worker_connections = 1000
max_requests = 1000  # Recycle workers after this many requests
max_requests_jitter = 50
timeout = int(os.getenv('GUNICORN_TIMEOUT', '120'))
graceful_timeout = int(os.getenv('GUNICORN_GRACEFUL_TIMEOUT', '30'))
keepalive = 2
preload_app = False

# Process naming
proc_name = 'restaurant_ai'

# Logging
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr
loglevel = os.getenv('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Security
limit_request_line = 4094
limit_request_fields = 100

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = '/path/to/key.pem'
# certfile = '/path/to/cert.pem'

def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    from app.extensions import db
    db.session.remove()
