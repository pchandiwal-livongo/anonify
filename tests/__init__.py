"""
Test suite for the anonify package.

This package contains comprehensive unit tests for all anonify functionality including:
- Core anonymization modules (faker, hasher, nuller, obfuscate, randomizer)
- Analysis modules (scoring, visualizer, reporter)
- Utility functions (logging, preprocessing)
- Main interface and CLI functionality
- Edge cases and error handling
"""

import os
import sys
import unittest

# Add the parent directory to the path so we can import anonify
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def load_tests(loader, start_dir, pattern):
    """Load all tests from the test directory."""
    suite = unittest.TestSuite()
    
    # Discover all tests in the tests directory
    test_loader = unittest.TestLoader()
    discovered_tests = test_loader.discover(
        start_dir=os.path.dirname(__file__),
        pattern='test_*.py',
        top_level_dir=os.path.dirname(__file__)
    )
    
    suite.addTests(discovered_tests)
    return suite 