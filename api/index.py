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

# Ensure the project root is on the path so 'config' can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.wsgi import application  # noqa: E402

# Vercel expects this name
app = application