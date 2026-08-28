"""Vercel serverless entry point for Django.

Vercel expects a module-level variable named `app` that is a WSGI
callable. We expose the Django WSGI application directly.

Note: Vercel runs this as a serverless function. Each request may
spin up a new container. The background thread for Gmail sync does
NOT run on Vercel (serverless has no long-running processes) - sync
must be triggered manually via the dashboard.
"""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Ensure the project root is on the path so 'config' can be imported.
# Vercel runs from the project root, but be explicit.
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

try:
    from config.wsgi import application  # noqa: E402
except Exception as exc:
    # Surface the error so Vercel logs show what failed at import time.
    sys.stderr.write(f"[api/index.py] Failed to import Django app: {exc}\n")
    raise

# Vercel expects the WSGI callable as 'app'
app = application