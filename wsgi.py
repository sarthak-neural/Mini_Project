"""
Production WSGI entrypoint.

Load the backend application module directly to avoid import ambiguity with the
root compatibility wrapper module.
"""

import importlib.util as _ilu
import os
import sys


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
BACKEND_APP_PATH = os.path.join(BACKEND_DIR, 'app.py')

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

_spec = _ilu.spec_from_file_location('backend_runtime_app_module', BACKEND_APP_PATH)
_backend_app = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_backend_app)

app = _backend_app.app


if __name__ == '__main__':
    app.run()
