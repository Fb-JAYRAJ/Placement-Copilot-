import os
import sys

# Ensure backend is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.ratelimit import limiter
from app.services.llm.provider import FakeProvider, set_llm_provider

# Always use FakeProvider in tests
set_llm_provider(FakeProvider())

# Disable rate limiter for tests
limiter.enabled = False
