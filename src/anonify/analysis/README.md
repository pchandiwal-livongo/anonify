# Anonify Analysis Module

![Mathematical](https://img.shields.io/badge/mathematics-statistical%20analysis-blue.svg)
![Algorithms](https://img.shields.io/badge/algorithms-distance%20metrics-green.svg)

This module provides comprehensive statistical analysis and scoring capabilities for evaluating data anonymization effectiveness. It implements mathematically rigorous metrics to quantify how well data has been de-identified.

## 📊 Overview

The analysis module consists of three main components:

- **`scoring.py`**: Statistical metrics and distance calculations
- **`visualizer.py`**: Interactive charts and data visualization
- **`reporter.py`**: Comprehensive HTML reports combining scoring and visualization

## 🧮 Scoring Methodology

Our scoring system implements a **three-step mathematical framework** to evaluate anonymization quality:

### **Step 1: Column-wise Distance Calculation**

Different data types require specialized distance metrics. We implement type-specific algorithms optimized for anonymization assessment.

#### **A. Categorical Columns**

##### **Cramér's V (Association Strength)**
Measures statistical association between original and de-identified categorical variables.

**Formula:**
```
V = √(χ² / n) / min(k-1, r-1)
```

Where:
- `χ²` = Chi-square statistic from contingency table
- `n` = Total number of samples
- `k` = Number of categories in original dataset  
- `r` = Number of categories in anonymized dataset

**Normalized Distance:**
```
D_cramer = 1 - V
```

- `V = 1`: Perfect association (poor anonymization)
- `V = 0`: Complete independence (excellent anonymization)

##### **Jaccard Distance (Set Similarity)**
Compares unique value sets between original and anonymized data.

**Formula:**
```
D_jaccard = 1 - |A ∩ B| / |A ∪ B|
```

Where:
- `A` = Set of unique values in original column
- `B` = Set of unique values in anonymized column
- `|A ∩ B|` = Size of intersection (common values)
- `|A ∪ B|` = Size of union (all unique values)

**Implementation:**
```python
def jaccard_distance(set_a, set_b):
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return 1 - (intersection / union) if union > 0 else 0
```

#### **B. Numeric Columns**

##### **Wasserstein Distance (Earth Mover's Distance)**
Measures the minimum cost to transform one distribution into another.

**Mathematical Definition:**
```
W(P, Q) = inf{γ∈Γ(P,Q)} ∫ |x - y| dγ(x,y)
```

**Normalized Form:**
```
D_wasserstein = W(P, Q) / R
```

Where:
- `P`, `Q` = Probability distributions of original and anonymized data
- `R` = Range of original column (max - min)
- `Γ(P,Q)` = Set of all couplings between P and Q

**Implementation:**
```python
from scipy.stats import wasserstein_distance

def normalized_wasserstein(original, anonymized):
    if len(original) == 0 or len(anonymized) == 0:
        return 1.0
    
    distance = wasserstein_distance(original, anonymized)
    range_val = np.max(original) - np.min(original)
    
    return min(distance / range_val, 1.0) if range_val > 0 else 0.0
```

##### **Kolmogorov-Smirnov Statistic**
Measures maximum difference between cumulative distribution functions.

**Formula:**
```
D_KS = sup_x |F_original(x) - F_anonymized(x)|
```

Where:
- `F_original(x)` = Empirical CDF of original data
- `F_anonymized(x)` = Empirical CDF of anonymized data
- `sup_x` = Supremum (maximum) over all x values

##### **Mean Shift Distance**
Standardized difference in means relative to original standard deviation.

**Formula:**
```
D_mean = |μ_original - μ_anonymized| / σ_original
```

Capped at 1.0 to maintain [0,1] normalization.

#### **C. Text Columns**

##### **Unique Value Replacement Rate**
Percentage of unique values that have been changed.

**Formula:**
```
D_unique = 1 - |U_original ∩ U_anonymized| / |U_original|
```

Where:
- `U_original` = Set of unique values in original text
- `U_anonymized` = Set of unique values in anonymized text

##### **Text Similarity Distance**
Based on string similarity metrics (Levenshtein, Jaro-Winkler).

**Average Similarity Approach:**
```python
def text_similarity_distance(original, anonymized):
    similarities = []
    
    for orig_val, anon_val in zip(original, anonymized):
        if pd.isna(orig_val) or pd.isna(anon_val):
            similarity = 0.0 if pd.isna(orig_val) != pd.isna(anon_val) else 1.0
        else:
            # Jaro-Winkler similarity
            similarity = jaro_winkler_similarity(str(orig_val), str(anon_val))
        
        similarities.append(similarity)
    
    avg_similarity = np.mean(similarities)
    return 1 - avg_similarity  # Convert to distance
```

### **Step 2: Column Distance Aggregation**

Each column type uses weighted averaging of its specific metrics:

#### **Categorical Columns:**
```
D_categorical = mean(D_cramer, D_jaccard)
```

#### **Numeric Columns:**
```
D_numeric = mean(D_wasserstein, D_KS, D_mean)
```

#### **Text Columns:**
```
D_text = mean(D_unique, D_similarity)
```

### **Step 3: Global Anonymization Score**

Final score aggregates all column distances using weighted mean:

**Formula:**
```
D_global = (1/N) × Σ(i=1 to N) w_i × D_i
```

Where:
- `N` = Total number of columns
- `D_i` = Normalized distance for column i
- `w_i` = Weight for column i (default = 1)

**Final Score (1-100 scale):**
```
anonify_score = 1 + 99 × D_global
```

**Interpretation:**
- **1-20**: Minimal anonymization (high risk)
- **21-50**: Moderate anonymization (medium risk)  
- **51-80**: Good anonymization (low risk)
- **81-100**: Excellent anonymization (very low risk)

## 🎯 Implementation Details

### **Robust Statistical Handling**

Our implementation includes several safeguards for real-world data:

```python
def safe_cramers_v(original, anonymized):
    """Cramér's V with edge case handling."""
    try:
        # Handle empty or single-value cases
        if len(original) == 0 or len(anonymized) == 0:
            return 0.0
            
        # Create contingency table
        contingency = pd.crosstab(original, anonymized)
        
        # Calculate chi-square
        chi2, _, _, _ = chi2_contingency(contingency)
        n = contingency.sum().sum()
        
        # Handle perfect independence
        if chi2 == 0:
            return 0.0
            
        # Calculate Cramér's V
        k, r = contingency.shape
        cramers_v = np.sqrt(chi2 / n) / np.sqrt(min(k-1, r-1))
        
        return min(cramers_v, 1.0)  # Cap at 1.0
        
    except Exception:
        return 0.0  # Conservative fallback
```

### **Performance Optimizations**

- **Vectorized Operations**: NumPy and pandas vectorization for large datasets
- **Memory Efficiency**: Streaming calculations for columns that don't fit in memory
- **Parallel Processing**: Multi-threaded computation for independent column calculations

### **Validation Framework**

Each metric includes validation tests:

```python
def test_metric_properties():
    """Ensure metrics satisfy mathematical properties."""
    # Symmetry: d(x,y) = d(y,x)
    # Triangle inequality: d(x,z) ≤ d(x,y) + d(y,z)  
    # Identity: d(x,x) = 0
    # Normalization: 0 ≤ d(x,y) ≤ 1
```

## 📈 Usage Examples

### **Basic Scoring**
```python
from anonify.analysis import AnonymizationScorer

scorer = AnonymizationScorer()
score = scorer.calculate_global_score(original_df, anonymized_df)
print(f"Anonymization Score: {score:.2f}/100")
```

### **Column-Level Analysis**
```python
column_scores = scorer.calculate_column_scores(original_df, anonymized_df)
for column, score in column_scores.items():
    print(f"{column}: {score:.2f}")
```

### **Custom Weights**
```python
weights = {'ssn': 2.0, 'name': 1.5, 'age': 1.0}  # Higher weight = more important
score = scorer.calculate_global_score(original_df, anonymized_df, weights=weights)
```

## 🔬 Research Background

Our scoring methodology is based on established research in:

- **Information Theory**: Mutual information and entropy measures
- **Statistical Distance**: Probability distribution comparison techniques  
- **Privacy Metrics**: Differential privacy and k-anonymity concepts
- **Machine Learning**: Feature similarity and data drift detection

### **Key References**
- Cramér, H. (1946). Mathematical Methods of Statistics
- Kantorovich, L. V. (1942). On the translocation of masses (Wasserstein distance)
- Kolmogorov, A. (1933). Sulla determinazione empirica di una legge di distribuzione
- Jaccard, P. (1912). The distribution of the flora in the alpine zone

## 🛠️ Advanced Configuration

### **Custom Distance Functions**
```python
def custom_numeric_distance(original, anonymized):
    """Example custom distance function."""
    # Your custom logic here
    return distance_value

scorer.register_custom_distance('numeric', custom_numeric_distance)
```

### **Sampling for Large Datasets**
```python
# For datasets > 1M rows, use sampling
scorer = AnonymizationScorer(sample_size=100000, random_state=42)
```

## ⚠️ Limitations and Considerations

1. **Sample Size**: Metrics become more reliable with larger sample sizes (n > 100 recommended)
2. **Data Distribution**: Highly skewed distributions may require specialized handling
3. **Correlation**: Score doesn't capture inter-column relationships
4. **Context Sensitivity**: Business context may require custom weighting schemes

## 🔮 Future Enhancements

- **Mutual Information**: Cross-column dependency analysis
- **Differential Privacy**: ε-differential privacy compliance scoring
- **Time Series**: Specialized metrics for temporal data
- **Graph Data**: Network anonymization assessment
- **Deep Learning**: Neural network-based similarity measures

---

For detailed API documentation, see the individual module docstrings in `scoring.py`, `visualizer.py`, and `reporter.py`. 