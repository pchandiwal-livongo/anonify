# Anonify

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![PyPI](https://img.shields.io/pypi/v/anonify.svg)

A comprehensive Python package for data de-identification with built-in scoring, visualization, and reporting capabilities. Designed following modern Python packaging standards for reliability and ease of use.

## 🚀 Features

- **Data Obfuscation**: Replace sensitive data with realistic but non-sensitive equivalents
- **Hashing**: Securely hash sensitive data columns with cryptographic functions
- **Nullification**: Replace data with null values for complete anonymization
- **Randomization**: Randomize data to preserve patterns without revealing actual values
- **Statistical Scoring**: Quantify anonymization effectiveness with mathematical metrics
- **Visualization**: Generate interactive charts comparing original vs anonymized data
- **Comprehensive Reporting**: Automated reports with scoring and visualizations
- **Audit Logging**: Integrated logging for tracking all transformation steps

## 🎯 Why Anonify?

Protecting sensitive data is not just compliance—it's trust. Anonify helps you easily anonymize and de-identify tabular data, so you can share, analyze, and develop without exposing real personal information.

### Key Capabilities

- **Column-wise De-identification**: Specify treatment for each column via YAML config
- **Flexible Inputs**: Accepts both pandas and Spark DataFrames
- **Configurable Workflows**: Use YAML configs for repeatable, transparent processes
- **Statistical Validation**: Built-in metrics to verify anonymization quality
- **Modern Python**: Built with current packaging standards and best practices

## 📦 Installation

### For Users

Install the latest stable version from PyPI:

```bash
pip install anonify
```

### For Developers

1. **Clone the repository:**
```bash
git clone https://github.com/pchandiwal-livongo/anonify.git
cd anonify
```

2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install in development mode:**
```bash
# Install with all development dependencies
pip install -e .[dev]

# Or install with specific feature sets
pip install -e .[visualization]  # For plotting features
pip install -e .                 # Core functionality only
```

## 🛠️ Supported Anonymization Methods

| Method | Description |
|--------|-------------|
| `fake` | Replace with realistic fake values (using Faker) |
| `hash` | Replace with cryptographic hash of value + salt |
| `null_column` | Replace entire column with null values |
| `randomize` | Replace with random/weighted values from list |
| `obfuscate` | Obfuscate values (e.g., shift dates, add noise) |
| `do_not_change` | Leave column untouched |

## ⚡ Quick Start

```python
import anonify
import pandas as pd

# Load your data
df = pd.read_csv('sensitive_data.csv')

# Quick anonymization
anonymized_df = anonify.deidentify(df, {
    'name': {'method': 'fake', 'fake_type': 'name'},
    'email': {'method': 'hash'},
    'ssn': {'method': 'null_column'},
    'salary': {'method': 'randomize', 'values': [30000, 50000, 70000, 90000]}
})

# Generate anonymization report
report = anonify.generate_quick_report(df, anonymized_df, output_path='anonymization_report.html')
```

## 🔬 Advanced Features

- **Spark Support**: Use the same config to anonymize `pyspark.sql.DataFrame` for big data
- **Custom Functions**: Register your own anonymization logic per column
- **Multi-level Audit Logging**: Output logs in JSON, CSV, or database formats
- **Batch Processing**: Process large files in chunks for memory efficiency
- **Reversible Hashing**: Optionally use keyed hash for reversible pseudonymization
- **Sensitive Data Detection**: Automatic scanner suggests columns that may need protection
- **Compliance Ready**: Designed with HIPAA/GDPR requirements in mind

## Scoring
## Scoring Methodology

### Step 1: Column-wise Distance Calculation

#### A. Categorical Columns

- **Cramér’s V**:  
  Measures association between original and de-identified columns.  
  - Formula:  
    \( V = \sqrt{ \frac{\chi^2 / n}{\min(k-1, r-1)} } \)
    - \( \chi^2 \): chi-square statistic  
    - \( n \): number of samples  
    - \( k, r \): number of categories in each dataset  
  - **Normalized Distance**: \( 1 - V \)  
    (V=1 means perfect association, V=0 means independence)

- **Jaccard Distance** (for unique value sets):  
  \( d_J(A, B) = 1 - \frac{|A \cap B|}{|A \cup B|} \)  
  Normalized between 0 and 1.

#### B. Numeric Columns

- **Wasserstein Distance** (“Earth Mover’s”):  
  \( W(P, Q) = \inf_{\gamma \in \Gamma(P, Q)} \int |x - y| d\gamma(x, y) \)  
  Normalize by the range:  
  \( D_{num} = \frac{W(P, Q)}{R} \)  
  (\( R \): range of original column)

- **Kolmogorov-Smirnov Statistic**:  
  \( D_{KS} = \sup_x |F_{orig}(x) - F_{deid}(x)| \)  
  Normalized between 0 and 1.

- **Mean Shift**:  
  \( D_{mean} = \frac{|mean_{orig} - mean_{deid}|}{std_{orig}} \)  
  Clip or cap at 1 if necessary.

#### C. Text Columns

- **% of Unique Values Replaced**:  
  \( D_{uniq} = 1 - \frac{|U_{orig} \cap U_{deid}|}{|U_{orig}|} \)

- **Levenshtein or Jaro Similarity**:  
  For each value pair, compute similarity.  
  **Distance:** \( D_{text} = 1 - \text{average similarity} \)

---

### Step 2: Column Distance Aggregation

- For **categorical** columns:  
  \( D_{cat} = mean(1 - V, d_J) \)

- For **numeric** columns:  
  \( D_{num} = mean(\text{normalized Wasserstein}, D_{KS}, D_{mean}) \)

- For **text** columns:  
  \( D_{text} = mean(D_{uniq}, D_{levenshtein}) \)

*All metrics are normalized to [0, 1].*

---

### Step 3: Global Anonymization Score

Aggregate all columns using a weighted mean:

\[
D_{global} = \frac{1}{N} \sum_{i=1}^N w_i D_i
\]

- \( N \): total columns  
- \( D_i \): normalized distance for column \( i \)  
- \( w_i \): column weight (default = 1)

**Final Score (scaled to 1–100):**

\[
\text{anonify\_score} = 1 + 99 \times D_{global}
\]

- **1**: Original and anonymized are almost identical
- **100**: No recognizable link between original and anonymized data

---

## 📁 Project Structure

Following modern Python packaging standards with src layout:

```
anonify/
├── src/
│   └── anonify/             # Main package (src layout)
│       ├── __init__.py      # Package interface
│       ├── main.py          # CLI interface and main functions
│       ├── preprocessor.py  # Data preprocessing utilities
│       ├── modules/         # Core anonymization methods
│       │   ├── __init__.py
│       │   ├── faker.py     # Fake data generation
│       │   ├── hasher.py    # Cryptographic hashing
│       │   ├── nuller.py    # Nullification methods
│       │   ├── obfuscate.py # Data obfuscation
│       │   └── randomizer.py # Randomization methods
│       ├── analysis/        # Analysis and reporting tools
│       │   ├── __init__.py
│       │   ├── scoring.py   # Statistical scoring metrics
│       │   ├── visualizer.py # Data visualization
│       │   └── reporter.py  # Report generation
│       └── utils/           # Utility functions
│           ├── __init__.py
│           └── logger.py    # Logging and audit trails
├── tests/                   # Test suite
├── pyproject.toml          # Modern project configuration
├── setup.py               # Minimal setup for compatibility
├── LICENSE                # MIT License
├── README.md             # This file
└── MANIFEST.in          # Package data specification
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/anonify --cov-report=html

# Run specific test modules
pytest tests/test_scoring.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes following the coding standards
4. Run tests: `pytest`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Repository**: [https://github.com/pchandiwal-livongo/anonify](https://github.com/pchandiwal-livongo/anonify)
- **Documentation**: [https://github.com/pchandiwal-livongo/anonify#readme](https://github.com/pchandiwal-livongo/anonify#readme)
- **Issues**: [https://github.com/pchandiwal-livongo/anonify/issues](https://github.com/pchandiwal-livongo/anonify/issues)

## 👤 Author

**Parag Chandiwal**
- Email: chandiwalp@gmail.com
- GitHub: [@pchandiwal-livongo](https://github.com/pchandiwal-livongo)

---

*Built with modern Python packaging standards and best practices.*


