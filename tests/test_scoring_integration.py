"""
Integration tests for the anonify scoring functionality.

Tests the actual working API to ensure scoring produces meaningful results
and provides useful feedback to users about anonymization quality.
"""

import unittest
import pandas as pd
import numpy as np
import os
import sys
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from anonify.analysis.scoring import AnonymizationScorer, quick_score
    from anonify.main import deidentify
    SCORING_AVAILABLE = True
except ImportError as e:
    SCORING_AVAILABLE = False
    print(f"Scoring functionality not available: {e}")


class TestScoringFunctionality(unittest.TestCase):
    """Test the actual scoring functionality with real data."""
    
    def setUp(self):
        """Set up test data for scoring validation."""
        if not SCORING_AVAILABLE:
            self.skipTest("Scoring module not available")
            
        # Create realistic test data
        np.random.seed(42)  # For reproducible tests
        
        self.original_data = pd.DataFrame({
            'employee_id': [f'EMP{i:03d}' for i in range(1, 101)],
            'name': [f'Person {i}' for i in range(1, 101)],
            'email': [f'person{i}@company.com' for i in range(1, 101)],
            'salary': np.random.normal(75000, 15000, 100),
            'department': np.random.choice(['IT', 'HR', 'Finance', 'Marketing'], 100),
            'birth_date': pd.date_range('1960-01-01', '2000-12-31', periods=100),
            'performance_score': np.random.uniform(1, 10, 100),
            'confidential_notes': [f'Confidential note {i}' for i in range(1, 101)]
        })
        
        self.scorer = AnonymizationScorer()
    
    def test_score_range_validation(self):
        """Test that scores are within expected 1-100 range."""
        # Create various levels of anonymization
        test_cases = [
            ('identical', self.original_data.copy()),
            ('slightly_modified', self.create_slightly_modified_data()),
            ('heavily_anonymized', self.create_heavily_anonymized_data())
        ]
        
        for case_name, anonymized_data in test_cases:
            with self.subTest(case=case_name):
                result = self.scorer.calculate_global_score(self.original_data, anonymized_data)
                
                # Verify score is in valid range
                score = result['anonify_score']
                self.assertGreaterEqual(score, 1, f"{case_name}: Score should be >= 1")
                self.assertLessEqual(score, 100, f"{case_name}: Score should be <= 100")
                
                # Verify result structure
                self.assertIn('global_distance', result)
                self.assertIn('column_scores', result)
                self.assertIn('column_types', result)
                self.assertIn('score_interpretation', result)
    
    def test_score_progression(self):
        """Test that scores increase with level of anonymization."""
        # Test identical data (should score low)
        identical_result = self.scorer.calculate_global_score(
            self.original_data, self.original_data.copy())
        
        # Test slightly modified data
        slightly_modified = self.create_slightly_modified_data()
        slight_result = self.scorer.calculate_global_score(
            self.original_data, slightly_modified)
        
        # Test heavily anonymized data
        heavily_anonymized = self.create_heavily_anonymized_data()
        heavy_result = self.scorer.calculate_global_score(
            self.original_data, heavily_anonymized)
        
        # Scores should increase with anonymization level
        identical_score = identical_result['anonify_score']
        slight_score = slight_result['anonify_score']
        heavy_score = heavy_result['anonify_score']
        
        self.assertLess(identical_score, slight_score, 
                       "Slightly modified data should score higher than identical")
        self.assertLess(slight_score, heavy_score,
                       "Heavily anonymized data should score highest")
        
        # Verify score interpretations make sense
        print(f"\nScore progression test results:")
        print(f"Identical: {identical_score:.1f} - {identical_result['score_interpretation']}")
        print(f"Slightly modified: {slight_score:.1f} - {slight_result['score_interpretation']}")
        print(f"Heavily anonymized: {heavy_score:.1f} - {heavy_result['score_interpretation']}")
    
    def test_column_wise_scoring(self):
        """Test that column-wise scores reflect anonymization levels."""
        # Create data where some columns are more anonymized than others
        mixed_anonymization = self.original_data.copy()
        
        # Heavily anonymize some columns
        mixed_anonymization['employee_id'] = ['ANON'] * 100  # Complete anonymization
        mixed_anonymization['name'] = [f'Anonymous {i}' for i in range(100)]  # Moderate anonymization
        # Leave other columns unchanged
        
        result = self.scorer.calculate_global_score(self.original_data, mixed_anonymization)
        column_scores = result['column_scores']
        
        # Heavily anonymized columns should score higher
        self.assertGreater(column_scores['employee_id'], column_scores['salary'],
                          "Heavily anonymized employee_id should score higher than unchanged salary")
        self.assertGreater(column_scores['name'], column_scores['department'],
                          "Moderately anonymized names should score higher than unchanged department")
        
        print(f"\nColumn-wise scoring results:")
        for col, score in column_scores.items():
            print(f"{col}: {score:.1f}")
    
    def test_quick_score_function(self):
        """Test the quick_score convenience function."""
        anonymized_data = self.create_heavily_anonymized_data()
        
        # Test quick_score function
        quick_result = quick_score(self.original_data, anonymized_data)
        
        # Compare with full scoring
        full_result = self.scorer.calculate_global_score(self.original_data, anonymized_data)
        
        self.assertAlmostEqual(quick_result['anonify_score'], full_result['anonify_score'], places=1,
                              msg="Quick score should match full score")
        
        # Verify it's a reasonable score
        self.assertGreater(float(quick_result['anonify_score']), 50, "Heavily anonymized data should score > 50")
        self.assertLessEqual(float(quick_result['anonify_score']), 100, "Score should not exceed 100")
    
    def test_statistical_methods(self):
        """Test individual statistical methods work correctly."""
        # Test Cramér's V
        cat_original = pd.Series(['A', 'B', 'C'] * 10)
        cat_identical = cat_original.copy()
        cat_different = pd.Series(['X', 'Y', 'Z'] * 10)
        
        # Identical should have high association (Cramér's V ≈ 1)
        cramers_identical = self.scorer.cramers_v(cat_original, cat_identical)
        self.assertGreater(cramers_identical, 0.95, "Identical categories should have high Cramér's V")
        
        # Different should have low association
        cramers_different = self.scorer.cramers_v(cat_original, cat_different)
        self.assertLess(cramers_different, 0.5, "Different categories should have low Cramér's V")
        
        # Test Wasserstein distance
        num_original = pd.Series(np.random.normal(100, 15, 50))
        num_similar = num_original + np.random.normal(0, 1, 50)  # Small noise
        num_different = pd.Series(np.random.normal(200, 30, 50))  # Different distribution
        
        distance_similar = self.scorer.wasserstein_distance_normalized(num_original, num_similar)
        distance_different = self.scorer.wasserstein_distance_normalized(num_original, num_different)
        
        self.assertLess(distance_similar, distance_different,
                       "Similar distributions should have smaller Wasserstein distance")
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test with empty dataframes
        empty_df = pd.DataFrame()
        try:
            result = self.scorer.calculate_global_score(empty_df, empty_df)
            # Should either handle gracefully or raise informative error
        except Exception as e:
            self.assertIsInstance(e, (ValueError, RuntimeError), 
                                f"Should raise ValueError or RuntimeError, got {type(e)}")
        
        # Test with single row
        single_row_original = self.original_data.iloc[:1].copy()
        single_row_anon = single_row_original.copy()
        single_row_anon['name'] = ['Anonymous']
        
        result = self.scorer.calculate_global_score(single_row_original, single_row_anon)
        self.assertIsNotNone(result['anonify_score'])
        
        # Test with all null data
        null_data = pd.DataFrame({'col1': [None, None, None], 'col2': [None, None, None]})
        try:
            result = self.scorer.calculate_global_score(null_data, null_data)
            # Should handle gracefully
            self.assertIsNotNone(result)
        except Exception as e:
            # Should provide informative error message
            self.assertIn('null', str(e).lower())
    
    def test_integration_with_main_deidentify(self):
        """Test scoring integration with main deidentify function."""
        try:
            # Create a simple config for testing
            config = {
                'columns': {
                    'employee_id': {'hash': {'salt': 'test_salt'}},
                    'name': {'fake': 'first_name'},
                    'email': {'hash': {'salt': 'email_salt'}},
                    'confidential_notes': {'null_column': True}
                }
            }
            
            # Run deidentification with scoring
            result = deidentify(self.original_data, config, return_scores=True)
            
            if isinstance(result, tuple):
                anonymized_data, scores = result
                
                # Verify we got meaningful scores
                self.assertIsInstance(scores, dict)
                self.assertIn('overall_score', scores)
                self.assertIn('column_scores', scores)
                
                # Verify scores are reasonable for this level of anonymization
                overall_score = scores['overall_score']
                self.assertGreater(overall_score, 30, 
                                 "Hash + fake + null should provide moderate anonymization")
                self.assertLess(overall_score, 95,
                               "Should not be perfect anonymization")
                
                print(f"\nIntegration test results:")
                print(f"Overall anonymization score: {overall_score:.1f}")
                print(f"Column scores: {scores.get('column_scores', {})}")
                
        except ImportError:
            self.skipTest("Main deidentify function not available")
    
    def create_slightly_modified_data(self):
        """Create data with minor modifications."""
        data = self.original_data.copy()
        # Add small noise to numerical columns
        data['salary'] = data['salary'] + np.random.normal(0, 100, 100)
        data['performance_score'] = data['performance_score'] + np.random.normal(0, 0.1, 100)
        # Make minor text changes
        data['email'] = data['email'].str.replace('@company.com', '@corp.com')
        return data
    
    def create_heavily_anonymized_data(self):
        """Create heavily anonymized data."""
        data = pd.DataFrame({
            'employee_id': ['ANON'] * 100,  # Completely anonymized
            'name': ['Anonymous'] * 100,    # Completely anonymized
            'email': ['anon@private.com'] * 100,  # Completely anonymized
            'salary': np.random.normal(50000, 20000, 100),  # Different distribution
            'department': np.random.choice(['DEPT_A', 'DEPT_B', 'DEPT_C'], 100),  # Different categories
            'birth_date': pd.date_range('1970-01-01', '1990-12-31', periods=100),  # Different range
            'performance_score': np.random.uniform(5, 15, 100),  # Different range
            'confidential_notes': [None] * 100  # Completely nullified
        })
        return data
    
    def test_user_interpretability(self):
        """Test that scoring results are interpretable and useful for users."""
        heavily_anonymized = self.create_heavily_anonymized_data()
        result = self.scorer.calculate_global_score(self.original_data, heavily_anonymized)
        
        # Test that interpretation is present and meaningful
        interpretation = result['score_interpretation']
        self.assertIsInstance(interpretation, str)
        self.assertGreater(len(interpretation), 10, "Interpretation should be descriptive")
        
        # Should mention anonymization level
        interpretation_lower = interpretation.lower()
        anonymization_keywords = ['anonymization', 'privacy', 'protection', 'low', 'medium', 'high']
        found_keywords = [kw for kw in anonymization_keywords if kw in interpretation_lower]
        self.assertGreater(len(found_keywords), 0, 
                          f"Interpretation should mention anonymization concepts. Found: {found_keywords}")
        
        print(f"\nUser interpretability test:")
        print(f"Score: {result['anonify_score']:.1f}")
        print(f"Interpretation: {interpretation}")
        print(f"Global distance: {result['global_distance']:.3f}")


if __name__ == '__main__':
    unittest.main(verbosity=2) 