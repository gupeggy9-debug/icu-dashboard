#!/usr/bin/env python
"""ICU Restaurant Dashboard - Production WSGI launcher."""
import os
import sys
import subprocess

port = os.environ.get("PORT", "5000")
bind = f"0.0.0.0:{port}"
cmd = ["gunicorn", "app:app", "--bind", bind, "--workers", "2", "--timeout", "120"]
print(f"Starting: {cmd}", flush=True)
os.execvp("gunicorn", cmd)
