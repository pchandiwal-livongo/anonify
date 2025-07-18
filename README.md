# Anonify

Anonify is a Python package designed for data de-identification, making it easier to anonymize sensitive information in datasets. It provides a range of modules for obfuscating, hashing, nullifying, and randomizing data columns.

## Features

- **Data Obfuscation**: Replace sensitive data with realistic but non-sensitive equivalents.
- **Hashing**: Securely hash sensitive data columns.
- **Nullification**: Replace data with null values for complete anonymization.
- **Randomization**: Randomize data to preserve patterns without revealing actual values.
- **Logging**: Integrated logging for tracking data processing steps.

anonify

The practical, modular, and auditable Python package for fast and flexible data de-identification.

Why anonify?

Protecting sensitive data is not just compliance—it’s trust. anonify helps you easily anonymize and de-identify tabular data, so you can share, analyze, and develop without exposing real personal information.

Key Features

Column-wise De-identification: Specify treatment for each column via YAML config.
Obfuscation: Replace real values with realistic fakes (e.g., names, addresses, dates).
Hashing: Cryptographically hash sensitive fields (with salt).
Nullification: Null out columns for strict privacy.
Randomization: Replace values with random (or weighted random) selections.
Logging & Audit Trails: Built-in logs track every transformation.
Report Generation: Quantify how well data is anonymized, and compare before/after.
Flexible Inputs: Accepts both pandas and Spark DataFrames.
Configurable: Use YAML configs for repeatable, transparent workflows.

## Supported Modes

Method	Description
fake	Replace with realistic fake values (using Faker).
hash	Replace with hash of value + salt.
null_column	Replace entire column with null values.
randomize	Replace with random/weighted values from list.
obfuscate	Obfuscate values (e.g. shift dates, add noise).
do_not_change	Leave column untouched.

## Advanced Features

Spark Support: Use the same config to anonymize pyspark.sql.DataFrame for big data.
Custom Functions: Register your own anonymization logic per column.
Multi-level Audit Logging: Output logs in JSON, CSV, or DB.
Batch Processing: Process large files in chunks.
Reversible Hashing: (Optionally) use keyed hash for reversible pseudonymization.
Sensitive Data Detection: Automatic scanner suggests columns that may need protection.
Anonymization Score Report: Statistical “difference” report (see below).
Compliance Ready: Designed with HIPAA/GDPR in mind; keep an audit trail.

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

## Installation

Anonify can be installed using pip:



```bash
pip install anonify
```

## Package Structure

After modularization, the anonify package is organized as follows:

```
anonify/
├── __init__.py              # Main package interface
├── main.py                  # CLI interface and main functions
├── preprocessor.py          # Data preprocessing utilities
├── modules/                 # Core anonymization methods
│   ├── __init__.py
│   ├── faker.py            # Fake data generation
│   ├── hasher.py           # Cryptographic hashing
│   ├── nuller.py           # Nullification methods
│   ├── obfuscate.py        # Data obfuscation
│   └── randomizer.py       # Randomization methods
├── analysis/                # Analysis and reporting tools
│   ├── __init__.py
│   ├── scoring.py          # Statistical scoring metrics
│   ├── visualizer.py       # Data visualization
│   └── reporter.py         # Report generation
└── utils/                   # Utility functions
    ├── __init__.py
    └── logger.py           # Logging and audit trails
```

## Installation

Anonify can be installed using pip:

```sh
