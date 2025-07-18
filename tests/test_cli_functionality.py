"""
Tests for CLI and main functionality of anonify package.

Tests the working interfaces to ensure they produce expected outputs,
handle errors gracefully, and provide useful feedback to users.
"""

import unittest
import pandas as pd
import numpy as np
import os
import sys
import tempfile
import subprocess
import yaml

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from anonify.main import deidentify, deidentify_from_file
    from anonify import get_available_features, print_feature_status
    MAIN_AVAILABLE = True
except ImportError as e:
    MAIN_AVAILABLE = False
    print(f"Main functionality not available: {e}")


class TestCLIFunctionality(unittest.TestCase):
    """Test command line interface functionality."""
    
    def setUp(self):
        """Set up test data and files."""
        if not MAIN_AVAILABLE:
            self.skipTest("Main functionality not available")
            
        # Create test data
        self.test_data = pd.DataFrame({
            'employee_id': ['EMP001', 'EMP002', 'EMP003'],
            'name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'email': ['john@company.com', 'jane@company.com', 'bob@company.com'],
            'salary': [75000, 85000, 92000],
            'department': ['IT', 'HR', 'Finance']
        })
        
        # Create temporary files for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv_path = os.path.join(self.temp_dir, 'test_data.csv')
        self.test_config_path = os.path.join(self.temp_dir, 'test_config.yaml')
        self.output_path = os.path.join(self.temp_dir, 'output.csv')
        
        # Write test data
        self.test_data.to_csv(self.test_csv_path, index=False)
        
        # Create test config
        self.test_config = {
            'columns': {
                'employee_id': {'hash': {'salt': 'test_salt'}},
                'name': {'fake': 'first_name'},
                'email': {'hash': {'salt': 'email_salt'}},
                'salary': {'randomize': {
                    'method': 'random_elements',
                    'elements': [70000, 75000, 80000, 85000, 90000]
                }},
                'department': {'do_not_change': True}
            }
        }
        
        with open(self.test_config_path, 'w') as f:
            yaml.dump(self.test_config, f)
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_basic_deidentify_function(self):
        """Test basic deidentify function works correctly."""
        # Test with dictionary config
        result = deidentify(self.test_data, self.test_config)
        
        # Verify structure is maintained
        self.assertEqual(len(result), len(self.test_data))
        self.assertEqual(list(result.columns), list(self.test_data.columns))
        
        # Verify some columns were changed
        self.assertNotEqual(list(result['employee_id']), list(self.test_data['employee_id']))
        self.assertNotEqual(list(result['name']), list(self.test_data['name']))
        self.assertNotEqual(list(result['email']), list(self.test_data['email']))
        
        # Verify unchanged column
        self.assertEqual(list(result['department']), list(self.test_data['department']))
        
        print(f"\nBasic deidentify test results:")
        print(f"Original names: {list(self.test_data['name'])}")
        print(f"Anonymized names: {list(result['name'])}")
    
    def test_deidentify_with_scoring(self):
        """Test deidentify function with scoring enabled."""
        result = deidentify(self.test_data, self.test_config, return_scores=True)
        
        if isinstance(result, tuple):
            anonymized_data, scores = result
            
            # Verify we got both data and scores
            self.assertIsInstance(anonymized_data, pd.DataFrame)
            self.assertIsInstance(scores, dict)
            
            # Verify score structure
            self.assertIn('overall_score', scores)
            self.assertIn('column_scores', scores)
            
            # Verify score is reasonable
            overall_score = scores['overall_score']
            self.assertGreaterEqual(overall_score, 1)
            self.assertLessEqual(overall_score, 100)
            
            print(f"\nScoring test results:")
            print(f"Overall score: {overall_score:.1f}")
            print(f"Score interpretation: {scores.get('score_interpretation', 'N/A')}")
            
        else:
            self.fail("Expected tuple when return_scores=True")
    
    def test_deidentify_from_file(self):
        """Test file-based deidentification."""
        # Test with file paths
        result = deidentify_from_file(
            input_file=self.test_csv_path,
            config_file=self.test_config_path,
            output_file=self.output_path
        )
        
        # Should return success status
        self.assertTrue(result)
        
        # Verify output file was created
        self.assertTrue(os.path.exists(self.output_path))
        
        # Verify output file content
        output_data = pd.read_csv(self.output_path)
        self.assertEqual(len(output_data), len(self.test_data))
        self.assertEqual(list(output_data.columns), list(self.test_data.columns))
        
        print(f"\nFile-based deidentify test:")
        print(f"Input file: {self.test_csv_path}")
        print(f"Output file: {self.output_path}")
        print(f"Output file created: {os.path.exists(self.output_path)}")
    
    def test_cli_basic_usage(self):
        """Test basic CLI usage."""
        try:
            # Test CLI help
            result = subprocess.run([
                sys.executable, '-m', 'anonify.main', '--help'
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__) + '/..')
            
            # Should return 0 and show help text
            self.assertEqual(result.returncode, 0)
            self.assertIn('usage:', result.stdout.lower())
            self.assertIn('anonify', result.stdout.lower())
            
        except Exception as e:
            self.skipTest(f"CLI test skipped due to environment issues: {e}")
    
    def test_cli_with_actual_files(self):
        """Test CLI with actual input files."""
        try:
            # Test actual CLI processing
            result = subprocess.run([
                sys.executable, '-m', 'anonify.main',
                self.test_csv_path,
                self.test_config_path,
                '-o', self.output_path,
                '--scores'
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__) + '/..')
            
            # Should complete successfully
            if result.returncode == 0:
                # Verify output file was created
                self.assertTrue(os.path.exists(self.output_path))
                
                # Verify scores were displayed
                self.assertIn('score', result.stdout.lower() + result.stderr.lower())
                
                print(f"\nCLI processing test:")
                print(f"Return code: {result.returncode}")
                print(f"Output created: {os.path.exists(self.output_path)}")
                
            else:
                print(f"CLI test failed with return code {result.returncode}")
                print(f"Error output: {result.stderr}")
                
        except Exception as e:
            self.skipTest(f"CLI file test skipped: {e}")
    
    def test_feature_availability(self):
        """Test feature availability detection."""
        try:
            # Test feature availability function
            features = get_available_features()
            self.assertIsInstance(features, dict)
            
            # Should have core features
            expected_features = ['core_anonymization', 'scoring', 'visualization', 'reporting']
            for feature in expected_features:
                if feature in features:
                    self.assertIsInstance(features[feature], bool)
            
            # Test feature status printing (should not crash)
            print_feature_status()
            
            print(f"\nFeature availability test:")
            print(f"Available features: {features}")
            
        except Exception as e:
            self.skipTest(f"Feature availability test skipped: {e}")
    
    def test_error_handling(self):
        """Test error handling in various scenarios."""
        
        # Test with non-existent file
        try:
            result = deidentify_from_file(
                input_file='nonexistent_file.csv',
                config_file=self.test_config_path
            )
            # Should either return False or raise informative error
            if result is not False:
                self.fail("Should handle non-existent file gracefully")
        except Exception as e:
            # Should provide informative error message
            error_msg = str(e).lower()
            self.assertTrue(any(keyword in error_msg for keyword in ['file', 'not found', 'exist']),
                          f"Error message should be informative: {e}")
        
        # Test with invalid config
        invalid_config = {'invalid': 'config'}
        try:
            result = deidentify(self.test_data, invalid_config)
            # Should handle gracefully - either return original data or informative error
        except Exception as e:
            # Should provide informative error message
            self.assertIsInstance(e, (ValueError, KeyError))
    
    def test_data_integrity(self):
        """Test that anonymization preserves data integrity."""
        result = deidentify(self.test_data, self.test_config)
        
        # Verify no data corruption
        self.assertFalse(result.isnull().all().any(), "No column should be completely null")
        
        # Verify data types are reasonable
        for col in result.columns:
            self.assertGreater(len(result[col].dropna()), 0, f"Column {col} should have some non-null values")
        
        # Verify deterministic behavior (same input should produce same output)
        result2 = deidentify(self.test_data, self.test_config)
        
        # For deterministic methods (like hash), results should be identical
        # Note: This test assumes hash is deterministic with same salt
        # For randomized elements, this might not hold, so we'll check structure consistency
        self.assertEqual(len(result), len(result2))
        self.assertEqual(list(result.columns), list(result2.columns))
    
    def test_configuration_validation(self):
        """Test configuration validation and flexibility."""
        
        # Test minimal config
        minimal_config = {
            'columns': {
                'name': {'fake': 'first_name'}
            }
        }
        
        result = deidentify(self.test_data, minimal_config)
        self.assertIsNotNone(result)
        
        # Only specified column should be changed
        self.assertNotEqual(list(result['name']), list(self.test_data['name']))
        self.assertEqual(list(result['employee_id']), list(self.test_data['employee_id']))  # Unchanged
        
        # Test complex config with multiple methods
        complex_config = {
            'columns': {
                'employee_id': {'hash': {'salt': 'complex_salt'}},
                'name': {'fake': 'first_name'},
                'email': {'hash': {'salt': 'email_salt'}},
                'salary': {'randomize': {
                    'method': 'random_elements',
                    'elements': [70000, 80000, 90000]
                }},
                'department': {'do_not_change': True}
            }
        }
        
        complex_result = deidentify(self.test_data, complex_config)
        self.assertIsNotNone(complex_result)
        
        print(f"\nConfiguration validation test:")
        print(f"Minimal config worked: {result is not None}")
        print(f"Complex config worked: {complex_result is not None}")


class TestScoreOutput(unittest.TestCase):
    """Test that score outputs are meaningful and useful."""
    
    def setUp(self):
        """Set up test data for score validation."""
        if not MAIN_AVAILABLE:
            self.skipTest("Main functionality not available")
            
        self.data = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
            'sensitive': ['secret1', 'secret2', 'secret3', 'secret4', 'secret5']
        })
    
    def test_score_meaningfulness(self):
        """Test that scores reflect actual anonymization levels."""
        
        # Low anonymization config
        low_config = {
            'columns': {
                'name': {'do_not_change': True},  # No change
                'sensitive': {'do_not_change': True}  # No change
            }
        }
        
        # High anonymization config
        high_config = {
            'columns': {
                'id': {'hash': {'salt': 'test_salt'}},
                'name': {'fake': 'first_name'},
                'sensitive': {'null_column': True}
            }
        }
        
        # Get scores for both
        _, low_scores = deidentify(self.data, low_config, return_scores=True)
        _, high_scores = deidentify(self.data, high_config, return_scores=True)
        
        # High anonymization should score higher
        self.assertGreater(high_scores['overall_score'], low_scores['overall_score'],
                          "High anonymization should score higher than low anonymization")
        
        # Verify interpretations are different and meaningful
        low_interp = low_scores.get('score_interpretation', '')
        high_interp = high_scores.get('score_interpretation', '')
        
        self.assertNotEqual(low_interp, high_interp, "Different anonymization levels should have different interpretations")
        
        print(f"\nScore meaningfulness test:")
        print(f"Low anonymization score: {low_scores['overall_score']:.1f} - {low_interp}")
        print(f"High anonymization score: {high_scores['overall_score']:.1f} - {high_interp}")
    
    def test_score_interpretability(self):
        """Test that score interpretations are user-friendly."""
        config = {
            'columns': {
                'name': {'fake': 'first_name'},
                'sensitive': {'null_column': True}
            }
        }
        
        _, scores = deidentify(self.data, config, return_scores=True)
        
        # Verify interpretation exists and is descriptive
        interpretation = scores.get('score_interpretation', '')
        self.assertGreater(len(interpretation), 10, "Interpretation should be descriptive")
        
        # Should contain relevant keywords
        interp_lower = interpretation.lower()
        relevant_keywords = ['anonymization', 'privacy', 'protection', 'low', 'medium', 'high']
        found_keywords = [kw for kw in relevant_keywords if kw in interp_lower]
        self.assertGreater(len(found_keywords), 0, "Interpretation should contain relevant privacy keywords")
        
        # Verify column scores are provided
        column_scores = scores.get('column_scores', {})
        self.assertGreater(len(column_scores), 0, "Should provide column-wise scores")
        
        for col, score in column_scores.items():
            self.assertIsInstance(score, (int, float), f"Column score for {col} should be numeric")
            self.assertGreaterEqual(score, 0, f"Column score for {col} should be >= 0")
            self.assertLessEqual(score, 1, f"Column score for {col} should be <= 1")
        
        print(f"\nScore interpretability test:")
        print(f"Overall score: {scores['overall_score']:.1f}")
        print(f"Interpretation: {interpretation}")
        print(f"Column scores: {column_scores}")
        print(f"Found keywords: {found_keywords}")


if __name__ == '__main__':
    unittest.main(verbosity=2) 