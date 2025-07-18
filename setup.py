#!/usr/bin/env python3
"""
Setup script for anonify package.

For modern installation, prefer using:
    pip install .

For development installation:
    pip install -e .[dev]
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name='anonify',
    use_scm_version=False,  # We define version in pyproject.toml
    packages=find_packages(exclude=['tests*', 'test*']),
    include_package_data=True,
    zip_safe=False,
    
    # Core dependencies - kept minimal for backward compatibility
    install_requires=[
        'pandas>=1.3.0',
        'pyyaml>=5.4.0',
        'faker>=13.0.0',
        'plotly>=5.0.0',
        'scipy>=1.7.0',
        'numpy>=1.21.0',
        'scikit-learn>=1.0.0',
    ],
    
    # Optional dependencies
    extras_require={
        'visualization': [
            'kaleido>=0.2.0',
            'dash>=2.0.0',
            'dash-bootstrap-components>=1.0.0',
        ],
        'dev': [
            'pytest>=6.0.0',
            'pytest-cov>=2.0.0',
            'black>=21.0.0',
            'flake8>=3.8.0',
            'mypy>=0.800',
            'build>=0.7.0',
            'twine>=3.0.0',
        ],
    },
    
    # Console scripts
    entry_points={
        'console_scripts': [
            'anonify=anonify.main:main',
            'anonify-report=anonify.main:generate_report_cli',
        ],
    },
    
    # Metadata
    author='Parag Chandiwal',
    author_email='chandiwalp@gmail.com',
    description='A comprehensive Python package for data de-identification with scoring and visualization',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/anonify',
    project_urls={
        'Documentation': 'https://github.com/yourusername/anonify#readme',
        'Source': 'https://github.com/yourusername/anonify',
        'Tracker': 'https://github.com/yourusername/anonify/issues',
    },
    
    # Classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Healthcare Industry',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Scientific/Engineering',
        'Topic :: Security',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Database',
        'Topic :: Office/Business',
    ],
    
    # Python version requirement
    python_requires='>=3.8',
    
    # Keywords
    keywords='data anonymization deidentification privacy gdpr hipaa data-science machine-learning statistics security',
    
    # Package data
    package_data={
        'anonify': ['py.typed'],
    },
)