"""
Unit tests for the scoring module.

Tests the AnonymizationScorer class and quick_score function to ensure:
- Statistical metrics are calculated correctly
- Scores are meaningful and within expected ranges
- Different data types are handled appropriately
- Edge cases are handled gracefully
"""

import unittest
import pandas as pd
import numpy as np
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from anonify.analysis.scoring import AnonymizationScorer, quick_score
    from anonify.modules.faker import fake_column
    from anonify.modules.hasher import hash_column
    from anonify.modules.nuller import null_column
    SCORING_AVAILABLE = True
except ImportError as e:
    SCORING_AVAILABLE = False
    print(f"Scoring module not available: {e}")


class TestAnonymizationScoring(unittest.TestCase):
    """Test case for anonymization scoring functionality."""
    
    def setUp(self):
        """Set up test data for scoring tests."""
        if not SCORING_AVAILABLE:
            self.skipTest("Scoring module not available")
            
        # Create comprehensive test dataset
        np.random.seed(42)  # For reproducible tests
        
        self.original_data = pd.DataFrame({
            # Categorical data
            'category': ['A', 'B', 'C', 'A', 'B', 'C'] * 10,
            'small_category': ['X', 'Y'] * 30,
            
            # Numerical data
            'normal_numeric': np.random.normal(100, 15, 60),
            'uniform_numeric': np.random.uniform(0, 100, 60),
            'integer_data': np.random.randint(1, 1000, 60),
            
            # Text data
            'names': [f'Person_{i}' for i in range(60)],
            'emails': [f'user{i}@domain.com' for i in range(60)],
            
            # Date data
            'dates': pd.date_range('2020-01-01', periods=60, freq='D'),
            
            # Mixed data with nulls
            'mixed_with_nulls': [None if i % 10 == 0 else f'Value_{i}' for i in range(60)]
        })
        
        # Create anonymized versions with different levels of anonymization
        self.create_anonymized_datasets()
        
        self.scorer = AnonymizationScorer()
    
    def create_anonymized_datasets(self):
        """Create different anonymized versions for testing."""
        
        # Low anonymization (minor changes)
        self.low_anon_data = self.original_data.copy()
        self.low_anon_data['category'] = self.low_anon_data['category'].str.lower()  # Minimal change
        self.low_anon_data['normal_numeric'] = self.low_anon_data['normal_numeric'] + 0.1  # Tiny noise
        
        # Medium anonymization
        self.medium_anon_data = self.original_data.copy()
        # Shuffle categorical but keep distribution
        np.random.seed(42)
        self.medium_anon_data['category'] = np.random.permutation(self.medium_anon_data['category'])
        # Add moderate noise to numeric
        self.medium_anon_data['normal_numeric'] = self.medium_anon_data['normal_numeric'] + np.random.normal(0, 5, 60)
        # Replace names with similar structure
        self.medium_anon_data['names'] = [f'Anon_{i}' for i in range(60)]
        
        # High anonymization (significant changes)
        self.high_anon_data = pd.DataFrame({
            'category': np.random.choice(['X', 'Y', 'Z'], 60),  # Different categories
            'small_category': np.random.choice(['P', 'Q', 'R'], 60),  # Different values
            'normal_numeric': np.random.normal(200, 30, 60),  # Different distribution
            'uniform_numeric': np.random.uniform(500, 1000, 60),  # Different range
            'integer_data': np.random.randint(5000, 10000, 60),  # Different range
            'names': ['Anonymous'] * 60,  # Completely anonymized
            'emails': ['anon@private.com'] * 60,  # Completely anonymized
            'dates': pd.date_range('2025-01-01', periods=60, freq='D'),  # Different period
            'mixed_with_nulls': [None] * 60  # All nullified
        })
    
    def test_scorer_initialization(self):
        """Test scorer initializes correctly."""
        scorer = AnonymizationScorer()
        self.assertIsNotNone(scorer)
        self.assertIsInstance(scorer.column_weights, dict)
        self.assertIsNone(scorer.global_score)
    
    def test_categorical_scoring_accuracy(self):
        """Test categorical data scoring accuracy using cramers_v method."""
        # Test with known data transformations
        original = pd.Series(['A', 'B', 'C'] * 20)
        
        # Case 1: Identical data (should have perfect association)
        identical = original.copy()
        cramers_v_score = self.scorer.cramers_v(original, identical)
        self.assertAlmostEqual(cramers_v_score, 1.0, places=2, 
                              msg="Identical categorical data should have Cramér's V ≈ 1")
        
        # Case 2: Completely different categories (should have low association)
        different = pd.Series(['X', 'Y', 'Z'] * 20)
        cramers_v_score = self.scorer.cramers_v(original, different)
        self.assertLess(cramers_v_score, 0.5, 
                       "Different categorical data should have low Cramér's V")
    
    def test_numerical_scoring_accuracy(self):
        """Test numerical data scoring accuracy."""
        original = pd.Series(np.random.normal(100, 15, 100))
        
        # Case 1: Nearly identical (small noise)
        near_identical = original + np.random.normal(0, 0.1, 100)
        score = self.scorer._score_numerical_column(original, near_identical)
        self.assertLess(score, 30, "Nearly identical numerical data should have low anonymization score")
        
        # Case 2: Moderate change (medium noise)
        moderate_change = original + np.random.normal(0, 10, 100)
        score = self.scorer._score_numerical_column(original, moderate_change)
        self.assertGreater(score, 20, "Moderately changed numerical data should have medium anonymization score")
        
        # Case 3: Different distribution
        different_dist = pd.Series(np.random.normal(200, 50, 100))
        score = self.scorer._score_numerical_column(original, different_dist)
        self.assertGreater(score, 60, "Different distribution should have high anonymization score")
    
    def test_text_scoring_accuracy(self):
        """Test text data scoring accuracy."""
        original = pd.Series([f'Person_{i}@company.com' for i in range(50)])
        
        # Case 1: Minor text changes
        minor_change = pd.Series([f'Person_{i}@company.org' for i in range(50)])  # Just domain change
        score = self.scorer._score_text_column(original, minor_change)
        self.assertLess(score, 50, "Minor text changes should have low-medium anonymization score")
        
        # Case 2: Completely different text
        different_text = pd.Series([f'Anonymous_{i}' for i in range(50)])
        score = self.scorer._score_text_column(original, different_text)
        self.assertGreater(score, 60, "Completely different text should have high anonymization score")
        
        # Case 3: All same value (complete anonymization)
        same_value = pd.Series(['Anonymous'] * 50)
        score = self.scorer._score_text_column(original, same_value)
        self.assertGreater(score, 80, "Same value for all should have very high anonymization score")
    
    def test_overall_scoring_ranges(self):
        """Test that overall scores fall within expected ranges."""
        
        # Test low anonymization
        scores_low = self.scorer.calculate_scores(self.original_data, self.low_anon_data)
        overall_low = scores_low['overall_score']
        self.assertGreaterEqual(overall_low, 1, "Score should be >= 1")
        self.assertLessEqual(overall_low, 100, "Score should be <= 100")
        self.assertLess(overall_low, 40, "Low anonymization should score < 40")
        
        # Test medium anonymization
        scores_medium = self.scorer.calculate_scores(self.original_data, self.medium_anon_data)
        overall_medium = scores_medium['overall_score']
        self.assertGreater(overall_medium, overall_low, "Medium anonymization should score higher than low")
        self.assertGreater(overall_medium, 30, "Medium anonymization should score > 30")
        self.assertLess(overall_medium, 80, "Medium anonymization should score < 80")
        
        # Test high anonymization
        scores_high = self.scorer.calculate_scores(self.original_data, self.high_anon_data)
        overall_high = scores_high['overall_score']
        self.assertGreater(overall_high, overall_medium, "High anonymization should score higher than medium")
        self.assertGreater(overall_high, 60, "High anonymization should score > 60")
    
    def test_score_interpretation(self):
        """Test score interpretation categories."""
        
        # Test interpretation function
        interpretations = [
            (5, "Very Low"),
            (25, "Low"), 
            (45, "Medium"),
            (65, "High"),
            (85, "Very High")
        ]
        
        for score, expected in interpretations:
            interpretation = self.scorer._interpret_score(score)
            self.assertIn(expected, interpretation, f"Score {score} should be interpreted as {expected}")
    
    def test_column_wise_scores(self):
        """Test that column-wise scores are reasonable."""
        scores = self.scorer.calculate_scores(self.original_data, self.high_anon_data)
        
        # Check that all columns have scores
        for col in self.original_data.columns:
            if col in self.high_anon_data.columns:
                self.assertIn(col, scores['column_scores'], f"Column {col} should have a score")
                score = scores['column_scores'][col]
                self.assertGreaterEqual(score, 1, f"Column {col} score should be >= 1")
                self.assertLessEqual(score, 100, f"Column {col} score should be <= 100")
    
    def test_quick_score_function(self):
        """Test the quick_score convenience function."""
        score = quick_score(self.original_data, self.medium_anon_data)
        
        self.assertIsInstance(score, (int, float), "Quick score should return a number")
        self.assertGreaterEqual(score, 1, "Quick score should be >= 1")
        self.assertLessEqual(score, 100, "Quick score should be <= 100")
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        
        # Test with empty dataframes
        empty_df = pd.DataFrame()
        with self.assertRaises(ValueError):
            self.scorer.calculate_scores(empty_df, empty_df)
        
        # Test with mismatched columns
        df1 = pd.DataFrame({'a': [1, 2, 3]})
        df2 = pd.DataFrame({'b': [4, 5, 6]})
        with self.assertRaises(ValueError):
            self.scorer.calculate_scores(df1, df2)
        
        # Test with all null columns
        null_original = pd.DataFrame({'col1': [None, None, None]})
        null_anon = pd.DataFrame({'col1': [None, None, None]})
        scores = self.scorer.calculate_scores(null_original, null_anon)
        self.assertIsNotNone(scores['overall_score'])
    
    def test_statistical_measures(self):
        """Test that statistical measures are calculated correctly."""
        # Create data with known statistical properties
        np.random.seed(42)
        original = pd.DataFrame({
            'numeric': np.random.normal(100, 15, 100),
            'categorical': ['A'] * 50 + ['B'] * 50
        })
        
        # Create anonymized version with known changes
        anonymized = pd.DataFrame({
            'numeric': np.random.normal(150, 20, 100),  # Different mean and std
            'categorical': ['C'] * 50 + ['D'] * 50  # Completely different categories
        })
        
        scores = self.scorer.calculate_scores(original, anonymized)
        
        # Verify scores reflect the significant changes
        self.assertGreater(scores['column_scores']['numeric'], 50, 
                          "Numerical column with different distribution should score high")
        self.assertGreater(scores['column_scores']['categorical'], 80, 
                          "Categorical column with different values should score very high")
    
    def test_real_world_anonymization_scenario(self):
        """Test scoring with real-world anonymization techniques."""
        # Create realistic original data
        original = pd.DataFrame({
            'name': ['John Doe', 'Jane Smith', 'Bob Johnson'] * 20,
            'email': ['john@email.com', 'jane@email.com', 'bob@email.com'] * 20,
            'salary': np.random.normal(75000, 15000, 60),
            'department': ['IT', 'HR', 'Finance'] * 20,
            'employee_id': range(1, 61)
        })
        
        # Apply realistic anonymization
        faker_module = FakerModule()
        hasher_module = HasherModule()
        nuller_module = NullerModule()
        
        anonymized = original.copy()
        
        # Anonymize using actual anonify modules
        anonymized['name'] = [faker_module.apply_faker({'fake': 'first_name'}, val) for val in original['name']]
        anonymized['email'] = [hasher_module.apply_hash({'hash': {'salt': 'test_salt'}}, val) for val in original['email']]
        anonymized['salary'] = original['salary'] + np.random.normal(0, 5000, 60)  # Add noise
        anonymized['department'] = original['department']  # Keep same
        anonymized['employee_id'] = [nuller_module.apply_null({'null_column': True}, val) for val in original['employee_id']]
        
        scores = self.scorer.calculate_scores(original, anonymized)
        
        # Verify realistic score ranges
        self.assertGreater(scores['overall_score'], 40, "Real anonymization should score reasonably high")
        self.assertLess(scores['overall_score'], 95, "Real anonymization shouldn't be perfect score")
        
        # Check individual columns
        self.assertGreater(scores['column_scores']['name'], 70, "Faked names should score high")
        self.assertGreater(scores['column_scores']['email'], 80, "Hashed emails should score very high")
        self.assertLess(scores['column_scores']['department'], 20, "Unchanged department should score low")
        self.assertGreater(scores['column_scores']['employee_id'], 90, "Nullified ID should score very high")


class TestScoringIntegration(unittest.TestCase):
    """Integration tests for scoring with other anonify components."""
    
    def setUp(self):
        """Set up integration test data."""
        if not SCORING_AVAILABLE:
            self.skipTest("Scoring module not available")
        
        # Use the actual test data from the project
        self.test_data_path = os.path.join(os.path.dirname(__file__), '../../test/data/dataframe1.csv')
        self.test_config_path = os.path.join(os.path.dirname(__file__), '../../test/config_files/dataframe1_config.yaml')
        
        if os.path.exists(self.test_data_path):
            self.test_data = pd.read_csv(self.test_data_path)
        else:
            # Create fallback test data if file doesn't exist
            self.test_data = pd.DataFrame({
                'external_id': ['ID1', 'ID2', 'ID3'],
                'first_name': ['John', 'Jane', 'Bob'],
                'last_name': ['Doe', 'Smith', 'Johnson'],
                'birth_date': ['1990-01-01', '1985-05-15', '1978-10-30'],
                'sensitive_info': ['info1', 'info2', 'info3']
            })
    
    def test_scoring_with_main_deidentify(self):
        """Test scoring integration with main deidentify function."""
        try:
            from anonify.main import deidentify
            
            # Create simple config
            config = {
                'columns': {
                    'external_id': {'hash': {'salt': 'test_salt'}},
                    'first_name': {'fake': 'first_name'},
                    'last_name': {'fake': 'last_name'}
                }
            }
            
            # Run anonymization with scoring
            result = deidentify(self.test_data, config, return_scores=True)
            
            if isinstance(result, tuple):
                anonymized_data, scores = result
                
                # Verify we got scores
                self.assertIsNotNone(scores)
                self.assertIn('overall_score', scores)
                self.assertIn('column_scores', scores)
                
                # Verify score reasonableness
                self.assertGreaterEqual(scores['overall_score'], 1)
                self.assertLessEqual(scores['overall_score'], 100)
                
        except ImportError:
            self.skipTest("Main module not available for integration test")


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2) 