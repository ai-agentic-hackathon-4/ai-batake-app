"""Pytest conftest.py - Ensure module identity for coverage tracking.

When tests import modules directly (e.g., 'from seed_service import ...'),
Python creates a SEPARATE module object from 'from backend.seed_service import ...'.
Coverage with 'source = backend' only tracks execution on the 'backend.seed_service'
module object. So we must ensure that 'seed_service' in sys.modules IS the same
object as 'backend.seed_service'.

Strategy: Pre-import all backend modules via the 'backend.' qualified path FIRST,
then register them under bare names too. This way all subsequent imports
(both 'import seed_service' and 'from backend.seed_service import ...')
get the SAME module object — the one coverage tracks.
"""
import sys
import importlib

# List of modules that might be imported directly without the 'backend.' prefix
_MODULE_NAMES = [
    'agent', 'character_service', 'db', 'diary_service',
    'image_service', 'logger', 'research_agent', 'seed_service',
]


def _preload_backend_modules():
    """Pre-import backend modules under qualified names and alias bare names to them."""
    for name in _MODULE_NAMES:
        qualified = f'backend.{name}'
        bare = name

        # Remove any previously loaded bare module to avoid stale references
        if bare in sys.modules and qualified not in sys.modules:
            del sys.modules[bare]

        try:
            mod = importlib.import_module(qualified)
        except Exception:
            continue

        # Register the qualified module under the bare name too
        sys.modules[bare] = mod


# Run at conftest load time (before any test module imports)
_preload_backend_modules()

# Debug: verify aliasing worked
import os as _os
if _os.environ.get('DEBUG_CONFTEST'):
    for name in _MODULE_NAMES:
        bare = sys.modules.get(name)
        qual = sys.modules.get(f'backend.{name}')
        same = bare is qual if (bare and qual) else 'N/A'
        print(f"[conftest] {name}: bare={bare is not None}, qual={qual is not None}, same={same}")
