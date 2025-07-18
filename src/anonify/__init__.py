"""
Anonify - Comprehensive Data De-identification Package

A practical, modular, and auditable Python package for fast and flexible 
data de-identification with built-in scoring and reporting capabilities.
"""

# Version info
__version__ = "0.2.0"
__author__ = "Parag Chandiwal"
__email__ = "chandiwalp@gmail.com"

# Core functionality
from .utils.logger import setup_logger
from .modules.faker import fake_column
from .modules.hasher import hash_column
from .modules.nuller import null_column
from .modules.randomizer import randomize_column
from .modules.obfuscate import obfuscate_column
from .preprocessor import preprocess

# Main interfaces
from .main import deidentify, deidentify_from_file, anonymize

# Advanced analysis features (with graceful fallbacks)
try:
    from .analysis import (
        AnonymizationScorer, quick_score,
        AnonymizationVisualizer, create_quick_visualization,
        AnonymizationReporter, generate_quick_report
    )
    __all_scoring__ = ['AnonymizationScorer', 'quick_score']
    __all_visualization__ = ['AnonymizationVisualizer', 'create_quick_visualization']
    __all_reporting__ = ['AnonymizationReporter', 'generate_quick_report']
except ImportError:
    __all_scoring__ = []
    __all_visualization__ = []
    __all_reporting__ = []

# Public API
__all__ = [
    # Core modules
    'setup_logger',
    'fake_column',
    'hash_column',
    'null_column',
    'randomize_column',
    'obfuscate_column',
    'preprocess',
    
    # Main interfaces
    'deidentify',
    'deidentify_from_file',
    'anonymize',  # Legacy name
    
    # Version info
    '__version__',
] + __all_scoring__ + __all_visualization__ + __all_reporting__


def get_available_features():
    """
    Get information about available features in this installation.
    
    Returns:
        Dictionary with feature availability status
    """
    features = {
        'core_anonymization': True,
        'scoring': len(__all_scoring__) > 0,
        'visualization': len(__all_visualization__) > 0,
        'reporting': len(__all_reporting__) > 0,
    }
    
    return features


def print_feature_status():
    """Print the status of available features."""
    features = get_available_features()
    
    print("🔐 Anonify Feature Status:")
    print(f"   ✅ Core Anonymization: {'Available' if features['core_anonymization'] else 'Not Available'}")
    print(f"   {'✅' if features['scoring'] else '❌'} Scoring & Metrics: {'Available' if features['scoring'] else 'Not Available'}")
    print(f"   {'✅' if features['visualization'] else '❌'} Visualization: {'Available' if features['visualization'] else 'Not Available'}")
    print(f"   {'✅' if features['reporting'] else '❌'} Report Generation: {'Available' if features['reporting'] else 'Not Available'}")
    
    if not all(features.values()):
        print("\n💡 To enable missing features, install additional dependencies:")
        if not features['scoring']:
            print("   pip install scipy scikit-learn")
        if not features['visualization']:
            print("   pip install plotly")
        if not features['reporting']:
            print("   pip install plotly scipy scikit-learn")


# Package metadata
__description__ = "Comprehensive data de-identification with scoring and reporting"
__url__ = "https://github.com/pchandiwal-livongo/anonify"
__license__ = "MIT"
__classifiers__ = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Operating System :: OS Independent",
    "Topic :: Scientific/Engineering",
    "Topic :: Security",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
