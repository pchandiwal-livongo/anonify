"""
Unit tests for anonify core anonymization modules.

Tests all the anonymization methods to ensure they produce expected outputs
and handle edge cases appropriately.
"""

import unittest
import pandas as pd
import numpy as np
import os
import sys
import hashlib
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from anonify.modules import faker, hasher, nuller, randomizer, obfuscate
    from anonify.main import deidentify
    MODULES_AVAILABLE = True
except ImportError as e:
    MODULES_AVAILABLE = False
    print(f"Modules not available: {e}")


class TestAnonymizationModules(unittest.TestCase):
    """Test core anonymization functionality."""
    
    def setUp(self):
        """Set up test data."""
        if not MODULES_AVAILABLE:
            self.skipTest("Anonymization modules not available")
            
        self.test_series = pd.Series(['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown'])
        self.test_numbers = pd.Series([100, 200, 300, 400, 500])
        self.test_emails = pd.Series(['john@example.com', 'jane@test.org', 'bob@company.net'])
    
    def test_hasher_module(self):
        """Test hash anonymization produces consistent, irreversible hashes."""
        # Test basic hashing
        hashed = hasher.hash_column(self.test_series, 'test_salt')
        
        # Should produce different values than original
        self.assertNotEqual(list(hashed), list(self.test_series))
        
        # Should be consistent - same input produces same hash
        hashed2 = hasher.hash_column(self.test_series, 'test_salt')
        self.assertEqual(list(hashed), list(hashed2))
        
        # Different salt should produce different hashes
        hashed_different_salt = hasher.hash_column(self.test_series, 'different_salt')
        self.assertNotEqual(list(hashed), list(hashed_different_salt))
        
        # Should produce valid SHA-256 hashes (64 characters, hex)
        for hash_value in hashed:
            self.assertEqual(len(hash_value), 64)
            self.assertTrue(all(c in '0123456789abcdef' for c in hash_value))
    
    def test_faker_module(self):
        """Test fake data generation produces realistic alternatives."""
        # Test various fake types
        fake_types_to_test = [
            ('first_name', self.test_series),
            ('last_name', self.test_series),
            ('email', self.test_emails),
        ]
        
        for fake_type, test_data in fake_types_to_test:
            with self.subTest(fake_type=fake_type):
                faked = faker.fake_column(test_data, fake_type)
                
                # Should produce different values than original
                self.assertNotEqual(list(faked), list(test_data))
                
                # Should produce same number of values
                self.assertEqual(len(faked), len(test_data))
                
                # Should not contain null values (faker generates real data)
                self.assertFalse(faked.isnull().any())
                
                # For first_name, should be reasonably short strings
                if fake_type == 'first_name':
                    for name in faked:
                        self.assertLess(len(name), 30, "First names should be reasonable length")
                        self.assertGreater(len(name), 1, "Names should not be empty")
    
    def test_nuller_module(self):
        """Test nullification completely removes data."""
        nulled = nuller.null_column(self.test_series)
        
        # All values should be null
        self.assertTrue(nulled.isnull().all())
        
        # Should maintain same length
        self.assertEqual(len(nulled), len(self.test_series))
        
        # Should work with any data type
        nulled_numbers = nuller.null_column(self.test_numbers)
        self.assertTrue(nulled_numbers.isnull().all())
    
    def test_randomizer_module(self):
        """Test randomization produces expected distributions."""
        # Test with provided elements
        elements = ['Option A', 'Option B', 'Option C']
        randomized = randomizer.randomize_column(self.test_series, elements)
        
        # All values should be from the provided elements
        unique_values = set(randomized.unique())
        self.assertTrue(unique_values.issubset(set(elements)))
        
        # Should maintain same length
        self.assertEqual(len(randomized), len(self.test_series))
        
        # Should not be identical to original (very high probability)
        self.assertNotEqual(list(randomized), list(self.test_series))
    
    def test_obfuscate_module(self):
        """Test obfuscation applies appropriate transformations."""
        # Test date shifting
        dates = pd.Series(pd.date_range('2020-01-01', periods=5))
        shifted_dates = obfuscate.shift_dates(dates, days=30)
        
        # Should shift by approximately the specified days
        original_date = dates.iloc[0]
        shifted_date = shifted_dates.iloc[0]
        day_diff = abs((shifted_date - original_date).days)
        self.assertLessEqual(day_diff, 35)  # Allow some randomness
        self.assertGreaterEqual(day_diff, 25)
        
        # Test numeric noise addition
        noise_added = obfuscate.add_numeric_noise(self.test_numbers, noise_percent=0.1)
        
        # Should be different but similar to original
        self.assertNotEqual(list(noise_added), list(self.test_numbers))
        
        # Should be within reasonable range (10% noise)
        for orig, noisy in zip(self.test_numbers, noise_added):
            percent_change = abs(noisy - orig) / orig
            self.assertLess(percent_change, 0.2, "Noise should be reasonable")


class TestMainIntegration(unittest.TestCase):
    """Test main deidentification integration with realistic scenarios."""
    
    def setUp(self):
        """Set up realistic test data."""
        if not MODULES_AVAILABLE:
            self.skipTest("Modules not available")
            
        self.employee_data = pd.DataFrame({
            'employee_id': ['EMP001', 'EMP002', 'EMP003', 'EMP004'],
            'first_name': ['John', 'Jane', 'Bob', 'Alice'],
            'last_name': ['Doe', 'Smith', 'Johnson', 'Brown'],
            'email': ['john.doe@company.com', 'jane.smith@company.com', 
                     'bob.johnson@company.com', 'alice.brown@company.com'],
            'salary': [75000, 85000, 92000, 78000],
            'department': ['IT', 'HR', 'Finance', 'IT'],
            'hire_date': ['2020-01-15', '2019-03-20', '2021-07-10', '2020-11-05'],
            'ssn': ['123-45-6789', '987-65-4321', '555-55-5555', '111-22-3333']
        })
    
    def test_comprehensive_anonymization(self):
        """Test comprehensive anonymization with multiple methods."""
        config = {
            'columns': {
                'employee_id': {'hash': {'salt': 'emp_salt'}},
                'first_name': {'fake': 'first_name'},
                'last_name': {'fake': 'last_name'},
                'email': {'hash': {'salt': 'email_salt'}},
                'salary': {'randomize': {
                    'method': 'random_elements',
                    'elements': [70000, 75000, 80000, 85000, 90000, 95000]
                }},
                'department': {'do_not_change': True},
                'hire_date': {'obfuscate': {'method': 'shift_dates', 'days': 90}},
                'ssn': {'null_column': True}
            }
        }
        
        anonymized = deidentify(self.employee_data, config)
        
        # Verify structure is maintained
        self.assertEqual(len(anonymized), len(self.employee_data))
        self.assertEqual(list(anonymized.columns), list(self.employee_data.columns))
        
        # Verify specific anonymization results
        
        # Hashed columns should be different but deterministic
        self.assertNotEqual(list(anonymized['employee_id']), list(self.employee_data['employee_id']))
        self.assertNotEqual(list(anonymized['email']), list(self.employee_data['email']))
        
        # Faked names should be different
        self.assertNotEqual(list(anonymized['first_name']), list(self.employee_data['first_name']))
        self.assertNotEqual(list(anonymized['last_name']), list(self.employee_data['last_name']))
        
        # Randomized salary should be from the provided list
        salary_options = {70000, 75000, 80000, 85000, 90000, 95000}
        for salary in anonymized['salary']:
            self.assertIn(salary, salary_options)
        
        # Department should be unchanged
        self.assertEqual(list(anonymized['department']), list(self.employee_data['department']))
        
        # SSN should be nullified
        self.assertTrue(anonymized['ssn'].isnull().all())
        
        print(f"\nComprehensive anonymization test results:")
        print(f"Original first names: {list(self.employee_data['first_name'])}")
        print(f"Anonymized first names: {list(anonymized['first_name'])}")
        print(f"Original salaries: {list(self.employee_data['salary'])}")
        print(f"Anonymized salaries: {list(anonymized['salary'])}")
    
    def test_anonymization_with_scoring(self):
        """Test anonymization produces reasonable quality scores."""
        config = {
            'columns': {
                'employee_id': {'hash': {'salt': 'test_salt'}},
                'first_name': {'fake': 'first_name'},
                'last_name': {'fake': 'last_name'},
                'email': {'hash': {'salt': 'email_salt'}},
                'ssn': {'null_column': True}
            }
        }
        
        result = deidentify(self.employee_data, config, return_scores=True)
        
        if isinstance(result, tuple):
            anonymized_data, scores = result
            
            # Should get reasonable overall score
            overall_score = scores['overall_score']
            self.assertGreater(overall_score, 50, "Should get high anonymization score")
            self.assertLess(overall_score, 95, "Should not be perfect score")
            
            # Column scores should reflect anonymization levels
            column_scores = scores['column_scores']
            
            # Nullified column should score very high
            self.assertGreater(column_scores['ssn'], 90, "Nullified SSN should score very high")
            
            # Hashed columns should score high
            self.assertGreater(column_scores['employee_id'], 70, "Hashed ID should score high")
            self.assertGreater(column_scores['email'], 70, "Hashed email should score high")
            
            # Unchanged columns should score low
            if 'department' in column_scores:
                self.assertLess(column_scores['department'], 20, "Unchanged department should score low")
            
            print(f"\nScoring integration test results:")
            print(f"Overall score: {overall_score:.1f}")
            print(f"Score interpretation: {scores.get('score_interpretation', 'N/A')}")
            print(f"Column scores: {column_scores}")
    
    def test_error_handling(self):
        """Test error handling with invalid configurations."""
        # Test with missing column in config
        config = {
            'columns': {
                'nonexistent_column': {'fake': 'first_name'}
            }
        }
        
        # Should handle gracefully or provide informative error
        try:
            result = deidentify(self.employee_data, config)
            # If it succeeds, should only process existing columns
            self.assertEqual(len(result), len(self.employee_data))
        except Exception as e:
            # Should provide informative error message
            self.assertIn('column', str(e).lower())
    
    def test_edge_cases_data_types(self):
        """Test handling of various data types and edge cases."""
        edge_case_data = pd.DataFrame({
            'mixed_nulls': ['value1', None, 'value3', None],
            'numbers': [1, 2, 3, 4],
            'floats': [1.1, 2.2, 3.3, 4.4],
            'dates': pd.date_range('2020-01-01', periods=4),
            'empty_strings': ['', 'value', '', 'another'],
        })
        
        config = {
            'columns': {
                'mixed_nulls': {'fake': 'word'},
                'numbers': {'hash': {'salt': 'num_salt'}},
                'floats': {'randomize': {'method': 'random_elements', 'elements': [1.0, 2.0, 3.0]}},
                'dates': {'obfuscate': {'method': 'shift_dates', 'days': 30}},
                'empty_strings': {'null_column': True}
            }
        }
        
        try:
            anonymized = deidentify(edge_case_data, config)
            
            # Should maintain data structure
            self.assertEqual(len(anonymized), len(edge_case_data))
            self.assertEqual(list(anonymized.columns), list(edge_case_data.columns))
            
            # Nullified column should be all null
            self.assertTrue(anonymized['empty_strings'].isnull().all())
            
            print(f"\nEdge cases test completed successfully")
            
        except Exception as e:
            # If there are issues, should provide clear error message
            self.fail(f"Edge case handling failed: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2) 