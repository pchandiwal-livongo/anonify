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

### Method 1: Direct Configuration

```python
import anonify
import pandas as pd

# Create sample data
data = {
    'name': ['Alice', 'Bob', 'Charlie'],
    'email': ['alice@example.com', 'bob@example.com', 'charlie@example.com'],
    'ssn': ['123-45-6789', '987-65-4321', '555-55-5555'],
    'salary': [50000, 60000, 70000]
}
df = pd.DataFrame(data)

# Direct method configuration
config = {
    'name': {'method': 'fake', 'fake_type': 'name'},
    'email': {'method': 'hash', 'salt': 'email_salt'},
    'ssn': {'method': 'null_column'},
    'salary': {'method': 'randomize', 'values': [30000, 50000, 70000, 90000]}
}

anonymized_df = anonify.deidentify(df, config)

print("Original data:")
print(df)
print("\nAnonymized data:")
print(anonymized_df)
```

### Method 2: YAML Configuration

First, create a YAML configuration file (`anonymization_config.yaml`):

```yaml
# Configuration for employee data anonymization
name:
  method: fake
  fake_type: name

email:
  method: hash
  salt: secure_email_salt

ssn:
  method: null_column

salary:
  method: randomize
  randomize_method: random_element
  values: [30000, 40000, 50000, 60000, 70000, 80000, 90000]

department:
  method: randomize
  randomize_method: random_elements
  values: ["Engineering", "Marketing", "Sales", "HR", "Finance"]
  weights: [0.3, 0.2, 0.2, 0.15, 0.15]
  length: 1
  unique: false

hire_date:
  method: obfuscate
  format: "%Y-%m-%d"
  threshold: 90
  min_range: "2020-01-01"
  max_range: "2024-12-31"
```

Then use it in your Python code:

```python
import anonify
import pandas as pd

# Load data
df = pd.read_csv('employee_data.csv')

# Method 1: Use YAML file path
anonymized_df = anonify.deidentify(df, 'anonymization_config.yaml')

# Method 2: Load YAML manually
import yaml
with open('anonymization_config.yaml', 'r') as file:
    config = yaml.safe_load(file)
anonymized_df = anonify.deidentify(df, config)

print(f"Anonymized {len(df)} records with {len(df.columns)} columns")
```

### Report Generation

```python
import anonify
import pandas as pd
import tempfile

# Create sample data
data = {
    'customer_id': [1, 2, 3, 4, 5],
    'name': ['Alice Johnson', 'Bob Smith', 'Carol Davis', 'David Wilson', 'Eva Brown'],
    'email': ['alice@email.com', 'bob@email.com', 'carol@email.com', 'david@email.com', 'eva@email.com'],
    'age': [28, 35, 42, 31, 29],
    'salary': [65000, 75000, 85000, 70000, 68000],
    'department': ['Engineering', 'Marketing', 'Sales', 'Engineering', 'HR']
}
df = pd.DataFrame(data)

# Anonymize the data
config = {
    'customer_id': {'method': 'hash', 'salt': 'customer_salt'},
    'name': {'method': 'fake', 'fake_type': 'name'},
    'email': {'method': 'hash', 'salt': 'email_salt'},
    'age': {'method': 'randomize', 'values': [25, 30, 35, 40, 45, 50]},
    'salary': {'method': 'obfuscate', 'noise_factor': 0.1},
    'department': {'method': 'do_not_change'}
}

anonymized_df = anonify.deidentify(df, config)

# Generate comprehensive report with scoring and visualizations
with tempfile.TemporaryDirectory() as temp_dir:
    try:
        report_path = anonify.generate_quick_report(
            original_df=df,
            anonymized_df=anonymized_df,
            config=config,
            dataset_name="Employee Dataset",
            output_dir=temp_dir
        )
        print(f"✓ Report generated: {report_path}")
        print("✓ Report includes:")
        print("  - Anonymization score and interpretation")
        print("  - Column-by-column analysis")
        print("  - Interactive visualizations")
        print("  - Statistical comparisons")
        
    except Exception as e:
        print(f"Report generation requires visualization dependencies: {e}")
        print("Install with: pip install anonify[visualization]")

# For production use, specify a permanent directory:
# report_path = anonify.generate_quick_report(
#     df, anonymized_df, config, output_dir="/path/to/reports"
# )
```

### CLI Usage

```bash
# Anonymize a CSV file using YAML configuration
python -m anonify data.csv config.yaml --output anonymized_data.csv

# Generate a report comparing original and anonymized data
python -m anonify report original.csv anonymized.csv -c config.yaml -o ./reports

# With additional options
python -m anonify data.csv config.yaml \
    --output anonymized_data.csv \
    --report \
    --report-dir ./reports \
    --verbose
```

## 🔬 Advanced Features

- **Spark Support**: Use the same config to anonymize `pyspark.sql.DataFrame` for big data
- **Custom Functions**: Register your own anonymization logic per column
- **Multi-level Audit Logging**: Output logs in JSON, CSV, or database formats
- **Batch Processing**: Process large files in chunks for memory efficiency
- **Reversible Hashing**: Optionally use keyed hash for reversible pseudonymization
- **Sensitive Data Detection**: Automatic scanner suggests columns that may need protection
- **Compliance Ready**: Designed with HIPAA/GDPR requirements in mind
## 📊 Anonymization Scoring Methodology

Anonify provides comprehensive statistical scoring to quantify anonymization effectiveness using a three-step mathematical framework:

### Step 1: Column-wise Distance Calculation

#### 🏷️ Categorical Columns

**Cramér's V** - Measures association between original and anonymized columns:

```
V = √(χ² / n) / min(k-1, r-1)
```
Where:
- `χ²` = chi-square statistic  
- `n` = number of samples  
- `k, r` = number of categories in each dataset  

**Normalized Distance**: `1 - V` (V=1 means perfect association, V=0 means independence)

**Jaccard Distance** - For unique value sets:

```
d_J(A, B) = 1 - |A ∩ B| / |A ∪ B|
```

Normalized between 0 and 1.

#### 🔢 Numeric Columns

**Wasserstein Distance** ("Earth Mover's Distance"):

```
W(P, Q) = minimum cost to transform distribution P into Q
D_num = W(P, Q) / R
```
Where `R` = range of original column

**Kolmogorov-Smirnov Statistic**:

```
D_KS = sup_x |F_original(x) - F_anonymized(x)|
```

**Mean Shift**:

```
D_mean = |mean_original - mean_anonymized| / std_original
```

#### 📝 Text Columns

**Percentage of Unique Values Replaced**:

```
D_unique = 1 - |U_original ∩ U_anonymized| / |U_original|
```

**Levenshtein/Jaro Similarity**:

```
D_text = 1 - average_similarity_score
```

### Step 2: Column Distance Aggregation

**Categorical columns**: `D_cat = mean(1 - V, d_J)`

**Numeric columns**: `D_num = mean(normalized_Wasserstein, D_KS, D_mean)`

**Text columns**: `D_text = mean(D_unique, D_levenshtein)`

*All metrics normalized to [0, 1]*

### Step 3: Global Anonymization Score

**Weighted Mean Across All Columns**:

```
D_global = (1/N) × Σ(w_i × D_i)
```

Where:
- `N` = total columns  
- `D_i` = normalized distance for column i  
- `w_i` = column weight (default = 1)

**Final Score (scaled to 1–100)**:

```
anonify_score = 1 + 99 × D_global
```

#### Score Interpretation:
- **1-20**: Minimal anonymization - data largely unchanged
- **21-40**: Low anonymization - some patterns preserved  
- **41-60**: Moderate anonymization - balanced privacy/utility
- **61-80**: High anonymization - strong privacy protection
- **81-100**: Maximum anonymization - no recognizable patterns 
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


