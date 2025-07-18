"""
Analysis package for data anonymization assessment.

This package provides functionality for:
- Scoring: Statistical metrics to assess anonymization quality
- Visualization: Charts and plots for data comparison
- Reporting: Comprehensive reports combining scoring and visualization
"""

# Import with graceful fallbacks for optional dependencies
try:
    from .scoring import AnonymizationScorer, quick_score
    SCORING_AVAILABLE = True
except ImportError:
    SCORING_AVAILABLE = False
    AnonymizationScorer = None
    quick_score = None

try:
    from .visualizer import AnonymizationVisualizer, create_quick_visualization
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    AnonymizationVisualizer = None
    create_quick_visualization = None

try:
    from .reporter import AnonymizationReporter, generate_quick_report
    REPORTING_AVAILABLE = True
except ImportError:
    REPORTING_AVAILABLE = False
    AnonymizationReporter = None
    generate_quick_report = None

__all__ = [
    'AnonymizationScorer',
    'quick_score',
    'AnonymizationVisualizer', 
    'create_quick_visualization',
    'AnonymizationReporter',
    'generate_quick_report',
    'SCORING_AVAILABLE',
    'VISUALIZATION_AVAILABLE',
    'REPORTING_AVAILABLE'
]

def get_available_analysis_features():
    """Get a dictionary of available analysis features."""
    return {
        'scoring': SCORING_AVAILABLE,
        'visualization': VISUALIZATION_AVAILABLE,
        'reporting': REPORTING_AVAILABLE
    }

def print_analysis_feature_status():
    """Print the status of available analysis features."""
    features = get_available_analysis_features()
    print("Analysis Features Status:")
    for feature, available in features.items():
        status = "✅" if available else "❌"
        print(f"  {feature.capitalize()}: {status}") 