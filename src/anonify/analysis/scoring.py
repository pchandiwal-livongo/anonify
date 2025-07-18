"""
Scoring module for anonify package.

This module implements various statistical metrics to measure the effectiveness
of data anonymization, including:
- Cramér's V for categorical data
- Wasserstein Distance for numerical data  
- Kolmogorov-Smirnov test for distribution comparison
- Jaccard Distance for set comparison
- Text similarity metrics
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import wasserstein_distance
# sklearn.metrics doesn't have cramers_v, we implement it ourselves
from collections import Counter
import difflib
from typing import Dict, List, Tuple, Union, Any
import warnings

warnings.filterwarnings('ignore')


class AnonymizationScorer:
    """Main class for computing anonymization scores."""
    
    def __init__(self, column_weights: Union[Dict[str, float], None] = None):
        """
        Initialize scorer with optional column weights.
        
        Args:
            column_weights: Dictionary mapping column names to weights (default: equal weights)
        """
        self.column_weights = column_weights if column_weights is not None else {}
        self.column_scores = {}
        self.global_score = None
        
    def cramers_v(self, x: pd.Series, y: pd.Series) -> float:
        """
        Calculate Cramér's V for categorical variables.
        
        Args:
            x: Original categorical series
            y: Anonymized categorical series
            
        Returns:
            Cramér's V value (0-1, where 1 indicates perfect association)
        """
        try:
            # Remove missing values from both series
            x_clean = x.dropna()
            y_clean = y.dropna()
            
            # Handle edge cases
            if len(x_clean) == 0 or len(y_clean) == 0:
                return 0.0
            
            if len(x_clean) != len(y_clean):
                # If lengths don't match after dropping NAs, align them
                min_len = min(len(x_clean), len(y_clean))
                x_clean = x_clean.iloc[:min_len]
                y_clean = y_clean.iloc[:min_len]
            
            # Check for constant columns (no variation)
            if len(x_clean.unique()) == 1 or len(y_clean.unique()) == 1:
                # If one column is constant, return 0 (no association)
                return 0.0
            
            # Create contingency table
            confusion_matrix = pd.crosstab(x_clean, y_clean)
            
            # Check if contingency table is valid
            if confusion_matrix.size == 0:
                return 0.0
            
            # Calculate chi-square statistic
            chi2_result = stats.chi2_contingency(confusion_matrix)
            chi2 = chi2_result[0]
            
            n = confusion_matrix.sum().sum()
            if n <= 1:
                return 0.0
            
            # Calculate basic Cramér's V
            r, k = confusion_matrix.shape
            
            # Handle edge case where one dimension is 1
            if r == 1 or k == 1:
                return 0.0
            
            # Apply bias correction (Bergsma & Wicher, 2013)
            phi2 = chi2 / n
            phi2corr = max(0, phi2 - ((k-1)*(r-1))/(n-1))
            rcorr = r - ((r-1)**2)/(n-1)
            kcorr = k - ((k-1)**2)/(n-1)
            
            # Ensure we don't divide by zero or negative values
            denominator = min((kcorr-1), (rcorr-1))
            if denominator <= 0:
                # Fall back to uncorrected Cramér's V
                denominator = min(k-1, r-1)
                if denominator <= 0:
                    return 0.0
                cramers_v = np.sqrt(phi2 / denominator)
            else:
                cramers_v = np.sqrt(phi2corr / denominator)
            
            # Ensure result is valid and in range [0, 1]
            if np.isnan(cramers_v) or np.isinf(cramers_v):
                return 0.0
            
            return max(0.0, min(1.0, float(cramers_v)))
            
        except (ValueError, ZeroDivisionError, TypeError, IndexError):
            return 0.0
    
    def jaccard_distance(self, x: pd.Series, y: pd.Series) -> float:
        """
        Calculate Jaccard distance between unique value sets.
        
        Args:
            x: Original series
            y: Anonymized series
            
        Returns:
            Jaccard distance (0-1, where 1 indicates no overlap)
        """
        set_x = set(x.dropna().unique())
        set_y = set(y.dropna().unique())
        
        if len(set_x) == 0 and len(set_y) == 0:
            return 0.0
        
        intersection = len(set_x.intersection(set_y))
        union = len(set_x.union(set_y))
        
        return 1 - (intersection / union) if union > 0 else 1.0
    
    def wasserstein_distance_normalized(self, x: pd.Series, y: pd.Series) -> float:
        """
        Calculate normalized Wasserstein distance for numerical data.
        
        Args:
            x: Original numerical series
            y: Anonymized numerical series
            
        Returns:
            Normalized Wasserstein distance (0-1)
        """
        try:
            x_clean = x.dropna().astype(float)
            y_clean = y.dropna().astype(float)
            
            if len(x_clean) == 0 or len(y_clean) == 0:
                return 1.0
                
            # Calculate Wasserstein distance
            wd = wasserstein_distance(x_clean, y_clean)
            
            # Normalize by range of original data
            x_range = x_clean.max() - x_clean.min()
            if x_range == 0:
                return 0.0 if wd == 0 else 1.0
                
            return min(1.0, wd / x_range)
        except:
            return 1.0
    
    def kolmogorov_smirnov_distance(self, x: pd.Series, y: pd.Series) -> float:
        """
        Calculate Kolmogorov-Smirnov distance for distribution comparison.
        
        Args:
            x: Original numerical series
            y: Anonymized numerical series
            
        Returns:
            KS statistic (0-1)
        """
        try:
            x_clean = x.dropna().astype(float)
            y_clean = y.dropna().astype(float)
            
            if len(x_clean) == 0 or len(y_clean) == 0:
                return 1.0
                
            ks_stat, _ = stats.ks_2samp(x_clean, y_clean)
            return ks_stat
        except:
            return 1.0
    
    def mean_shift_distance(self, x: pd.Series, y: pd.Series) -> float:
        """
        Calculate normalized mean shift distance.
        
        Args:
            x: Original numerical series
            y: Anonymized numerical series
            
        Returns:
            Normalized mean shift (0-1, capped at 1)
        """
        try:
            x_clean = x.dropna().astype(float)
            y_clean = y.dropna().astype(float)
            
            if len(x_clean) == 0 or len(y_clean) == 0:
                return 1.0
                
            mean_diff = abs(x_clean.mean() - y_clean.mean())
            x_std = x_clean.std()
            
            if x_std == 0:
                return 0.0 if mean_diff == 0 else 1.0
                
            return min(1.0, mean_diff / x_std)
        except:
            return 1.0
    
    def text_similarity_distance(self, x: pd.Series, y: pd.Series) -> float:
        """
        Calculate text similarity distance using multiple metrics.
        
        Args:
            x: Original text series
            y: Anonymized text series
            
        Returns:
            Combined text distance (0-1)
        """
        # Unique values replacement percentage
        x_unique = set(x.dropna().astype(str))
        y_unique = set(y.dropna().astype(str))
        
        if len(x_unique) == 0:
            unique_replacement_dist = 0.0
        else:
            common_values = len(x_unique.intersection(y_unique))
            unique_replacement_dist = 1 - (common_values / len(x_unique))
        
        # Average string similarity (using difflib)
        try:
            x_str = x.dropna().astype(str)
            y_str = y.dropna().astype(str)
            
            if len(x_str) == 0 or len(y_str) == 0:
                string_similarity_dist = 1.0
            else:
                similarities = []
                sample_size = min(len(x_str), len(y_str), 100)
                for i in range(sample_size):  # Sample for performance
                    try:
                        sim = difflib.SequenceMatcher(None, str(x_str.iloc[i]), str(y_str.iloc[i])).ratio()
                        similarities.append(sim)
                    except:
                        similarities.append(0.0)
                
                avg_similarity = np.mean(similarities) if similarities else 0.0
                string_similarity_dist = 1 - avg_similarity
        except:
            string_similarity_dist = 1.0
        
        # Combine metrics
        return np.mean([unique_replacement_dist, string_similarity_dist])
    
    def detect_column_type(self, series: pd.Series) -> str:
        """
        Detect the type of a pandas Series.
        
        Args:
            series: Input series
            
        Returns:
            Column type: 'categorical', 'numerical', or 'text'
        """
        # Remove nulls for analysis
        series_clean = series.dropna()
        
        if len(series_clean) == 0:
            return 'categorical'
        
        # Check if numerical
        try:
            pd.to_numeric(series_clean)
            return 'numerical'
        except:
            pass
        
        # Check if it's categorical (limited unique values relative to total)
        unique_ratio = len(series_clean.unique()) / len(series_clean)
        if unique_ratio < 0.5:  # Less than 50% unique values
            return 'categorical'
        else:
            return 'text'
    
    def calculate_column_distance(self, original: pd.Series, anonymized: pd.Series, 
                                column_name: Union[str, None] = None) -> float:
        """
        Calculate distance score for a single column.
        
        Args:
            original: Original column data
            anonymized: Anonymized column data
            column_name: Name of the column (for logging)
            
        Returns:
            Distance score (0-1, where 1 indicates maximum anonymization)
        """
        column_type = self.detect_column_type(original)
        
        if column_type == 'categorical':
            # For categorical: average of (1 - Cramér's V) and Jaccard distance
            cramers_distance = 1 - self.cramers_v(original, anonymized)
            jaccard_dist = self.jaccard_distance(original, anonymized)
            distance = np.mean([cramers_distance, jaccard_dist])
            
        elif column_type == 'numerical':
            # For numerical: average of Wasserstein, KS, and mean shift distances
            wasserstein_dist = self.wasserstein_distance_normalized(original, anonymized)
            ks_dist = self.kolmogorov_smirnov_distance(original, anonymized)
            mean_shift_dist = self.mean_shift_distance(original, anonymized)
            distance = float(np.mean([float(wasserstein_dist), float(ks_dist), float(mean_shift_dist)]))
            
        else:  # text
            distance = self.text_similarity_distance(original, anonymized)
        
        return distance
    
    def calculate_global_score(self, original_df: pd.DataFrame, 
                             anonymized_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate comprehensive anonymization score for entire dataset.
        
        Args:
            original_df: Original dataframe
            anonymized_df: Anonymized dataframe
            
        Returns:
            Dictionary containing detailed scoring results
        """
        if original_df.shape != anonymized_df.shape:
            raise ValueError("Original and anonymized dataframes must have the same shape")
        
        column_distances = {}
        column_types = {}
        
        # Calculate distance for each column
        for column in original_df.columns:
            if column in anonymized_df.columns:
                distance = self.calculate_column_distance(
                    original_df[column], 
                    anonymized_df[column], 
                    column
                )
                column_distances[column] = distance
                column_types[column] = self.detect_column_type(original_df[column])
        
        # Calculate weighted global distance
        total_weight = 0
        weighted_sum = 0
        
        for column, distance in column_distances.items():
            weight = self.column_weights.get(column, 1.0)
            weighted_sum += weight * distance
            total_weight += weight
        
        global_distance = weighted_sum / total_weight if total_weight > 0 else 0
        
        # Convert to 1-100 scale (as specified in README)
        anonify_score = 1 + 99 * global_distance
        
        # Store results
        self.column_scores = column_distances
        self.global_score = anonify_score
        
        return {
            'anonify_score': round(anonify_score, 2),
            'global_distance': round(global_distance, 4),
            'column_scores': {k: round(v, 4) for k, v in column_distances.items()},
            'column_types': column_types,
            'total_columns': len(column_distances),
            'score_interpretation': self._interpret_score(anonify_score)
        }
    
    def _interpret_score(self, score: float) -> str:
        """Provide interpretation of the anonymization score."""
        if score < 20:
            return "Very Low Anonymization - Data is largely unchanged"
        elif score < 40:
            return "Low Anonymization - Some changes but patterns remain"
        elif score < 60:
            return "Moderate Anonymization - Reasonable privacy protection"
        elif score < 80:
            return "High Anonymization - Strong privacy protection"
        else:
            return "Very High Anonymization - Maximum privacy protection"


def quick_score(original_df: pd.DataFrame, anonymized_df: pd.DataFrame, 
                column_weights: Union[Dict[str, float], None] = None) -> Dict[str, Any]:
    """
    Quick function to calculate anonymization score.
    
    Args:
        original_df: Original dataframe
        anonymized_df: Anonymized dataframe
        column_weights: Optional column weights
        
    Returns:
        Scoring results dictionary
    """
    scorer = AnonymizationScorer(column_weights)
    return scorer.calculate_global_score(original_df, anonymized_df) 