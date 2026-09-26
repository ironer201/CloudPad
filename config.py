"""Loads Supabase credentials from a .env file (standard library only).

Lookup order:
  1. Real environment variables (e.g. set in the shell) — highest priority
  2. The .env file sitting next to the app

If nothing is configured, values fall back to empty strings and the app
runs as a plain offline notepad — cloud actions show a friendly hint.
"""
import os
import sys

# In a PyInstaller build, __file__ lives inside the bundle — use the
# folder that contains the .exe / binary instead, so users can edit .env.
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ENV_FILE = os.path.join(BASE_DIR, ".env")


def load_env(path=ENV_FILE):
    """Tiny KEY=VALUE parser. Skips comments and blank lines."""
    try:
        with open(path, "r", encoding="utf-8-sig") as f:   # -sig strips BOM
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                # strip surrounding quotes if present: KEY="value" or KEY='value'
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                    value = value[1:-1]
                os.environ.setdefault(key, value)   # real env vars win
    except OSError:
        pass  # no .env file -> offline mode, handled gracefully


load_env()

SUPABASE_URL      = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

# True only when both values look usable (real anon keys are long JWTs,
# so this rejects empty values and leftover placeholders).
CLOUD_CONFIGURED = (SUPABASE_URL.startswith("https://")
                    and len(SUPABASE_ANON_KEY) > 40)