"""
Production WSGI entrypoint.

Use the compatibility root app instance so legacy route registrations defined
in backend/app.py remain available in deployed environments.
"""

from app import app


if __name__ == '__main__':
    app.run()
