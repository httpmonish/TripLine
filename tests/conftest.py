"""
conftest.py — pytest configuration for Tripline Phase 0 tests.

Adds the project root to sys.path so that armoriq_helper, server, etc.
can be imported from tests/test_phase0.py without packaging.
"""

import sys
import os

# Ensure the project root is first on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
