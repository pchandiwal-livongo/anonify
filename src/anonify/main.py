"""
Main module for anonify package.

This module provides the primary interface for data anonymization with 
scoring, reporting, and CLI functionality.
"""

import pandas as pd
import yaml
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any, Union, Optional

from .preprocessor import preprocess
from .utils.logger import setup_logger

# Import analysis modules with graceful fallbacks
try:
    from .analysis import (
        AnonymizationScorer, quick_score,
        AnonymizationVisualizer, create_quick_visualization,
        AnonymizationReporter, generate_quick_report,
        SCORING_AVAILABLE, VISUALIZATION_AVAILABLE, REPORTING_AVAILABLE
    )
except ImportError:
    SCORING_AVAILABLE = False
    VISUALIZATION_AVAILABLE = False 
    REPORTING_AVAILABLE = False
    AnonymizationScorer = None
    quick_score = None
    AnonymizationVisualizer = None
    create_quick_visualization = None
    AnonymizationReporter = None
    generate_quick_report = None


def deidentify(dataframe: pd.DataFrame, 
               yaml_config: Union[str, Dict[str, Any]], 
               return_scores: bool = False,
               generate_report: bool = False,
               dataset_name: Union[str, None] = None,
               report_output_dir: Union[str, None] = None) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Main function to de-identify a pandas DataFrame.
    
    Args:
        dataframe: Input pandas DataFrame to anonymize
        yaml_config: Path to YAML configuration file or config dictionary
        return_scores: Whether to return scoring metrics along with anonymized data
        generate_report: Whether to generate a comprehensive report
        dataset_name: Name of the dataset to include in report title
        report_output_dir: Directory to save reports
        
    Returns:
        Anonymized DataFrame, or dictionary with DataFrame and additional info
    """
    logger = setup_logger(__name__)
    logger.info("Starting data de-identification process")
    
    # Load configuration
    if isinstance(yaml_config, str):
        with open(yaml_config, 'r') as file:
            config = yaml.safe_load(file)
        logger.info(f"Loaded configuration from {yaml_config}")
    else:
        config = yaml_config
        logger.info("Using provided configuration dictionary")
    
    # Handle both direct column config and wrapped config formats
    if 'columns' not in config:
        # Direct format: {'col1': {'method': 'fake'}, 'col2': {'method': 'hash'}}
        # Convert to expected format: {'columns': {'col1': {'method': 'fake'}, ...}}
        formatted_config = {'columns': {}}
        for column_name, column_config in config.items():
            if isinstance(column_config, dict) and 'method' in column_config:
                # Convert method-based config to action-based config
                method = column_config['method']
                method_params = {k: v for k, v in column_config.items() if k != 'method'}
                
                # Handle special cases for different methods
                if method == 'fake':
                    # For fake method, use the fake_type directly as the value
                    fake_type = method_params.get('fake_type', 'name')
                    formatted_config['columns'][column_name] = {method: fake_type}
                elif method == 'randomize':
                    # For randomize, map the user-friendly params to expected structure
                    randomize_params = {}
                    # Default to random_element if no randomize_method specified
                    randomize_params['method'] = method_params.get('randomize_method', 'random_element')
                    if 'values' in method_params:
                        randomize_params['elements'] = method_params['values']
                    # Copy other parameters as-is
                    for key, value in method_params.items():
                        if key not in ['randomize_method', 'values']:
                            randomize_params[key] = value
                    formatted_config['columns'][column_name] = {method: randomize_params}
                elif method == 'null_column':
                    # For null_column, use boolean value
                    formatted_config['columns'][column_name] = {method: True}
                elif method == 'do_not_change':
                    # For do_not_change, use boolean value
                    formatted_config['columns'][column_name] = {method: True}
                else:
                    # For other methods (hash, obfuscate), use params as-is
                    formatted_config['columns'][column_name] = {method: method_params}
        config = formatted_config
        logger.info("Converted direct column configuration to expected format")
    
    # Store original for comparison
    original_df = dataframe.copy()
    
    # Create a copy for anonymization (preserve original)
    dataframe_copy = dataframe.copy()
    
    # Perform anonymization
    logger.info(f"Processing {len(dataframe)} records with {len(dataframe.columns)} columns")
    anonymized_df = preprocess(dataframe_copy, config)
    logger.info("De-identification completed")
    
    # Prepare return value
    result = anonymized_df
    
    # Calculate scores if requested or needed for reporting
    if (return_scores or generate_report) and SCORING_AVAILABLE:
        logger.info("Calculating anonymization scores")
        scores = quick_score(original_df, anonymized_df)
        logger.info(f"Anonymization score: {scores['anonify_score']:.2f}")
        
        if return_scores:
            result = {
                'anonymized_data': anonymized_df,
                'scores': scores,
                'config': config
            }
    
    # Generate report if requested
    if generate_report and REPORTING_AVAILABLE:
        logger.info("Generating anonymization report")
        try:
            report_path = generate_quick_report(
                original_df, 
                anonymized_df, 
                config, 
                dataset_name=dataset_name,
                output_dir=report_output_dir
            )
            logger.info(f"Report generated: {report_path}")
            
            if isinstance(result, dict):
                result['report_path'] = report_path
            else:
                result = {
                    'anonymized_data': result,
                    'report_path': report_path
                }
        except Exception as e:
            logger.warning(f"Report generation failed: {e}")
    
    return result


def deidentify_from_file(input_file: str, 
                        config_file: str,
                        output_file: Union[str, None] = None,
                        return_scores: bool = False,
                        generate_report: bool = False,
                        report_output_dir: Union[str, None] = None) -> Union[str, Dict[str, Any]]:
    """
    De-identify data from a file.
    
    Args:
        input_file: Path to input CSV file
        config_file: Path to YAML configuration file
        output_file: Path to output CSV file (optional)
        return_scores: Whether to return scoring metrics
        generate_report: Whether to generate a comprehensive report
        report_output_dir: Directory to save reports
        
    Returns:
        Path to output file or dictionary with results
    """
    logger = setup_logger(__name__)
    
    # Read input data
    logger.info(f"Reading data from {input_file}")
    df = pd.read_csv(input_file)
    
    # Extract dataset name from input file path
    input_path = Path(input_file)
    dataset_name = input_path.stem  # Get filename without extension
    
    # Process data
    result = deidentify(
        df, 
        config_file, 
        return_scores=return_scores,
        generate_report=generate_report,
        dataset_name=dataset_name,
        report_output_dir=report_output_dir
    )
    
    # Extract anonymized data
    if isinstance(result, dict):
        anonymized_df = result['anonymized_data']
    else:
        anonymized_df = result
    
    # Save output
    if output_file is None:
        output_file = str(input_path.parent / f"{input_path.stem}_anonymized{input_path.suffix}")
    
    anonymized_df.to_csv(output_file, index=False)
    logger.info(f"Anonymized data saved to {output_file}")
    
    if isinstance(result, dict):
        result['output_file'] = output_file
        return result
    else:
        return output_file


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Anonify - Comprehensive Data De-identification Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  anonify data.csv config.yaml                    # Basic anonymization
  anonify data.csv config.yaml -o output.csv      # Specify output file
  anonify data.csv config.yaml --scores           # Include scoring metrics
  anonify data.csv config.yaml --report           # Generate HTML report
  anonify data.csv config.yaml --scores --report  # Full analysis with report
        """
    )
    
    parser.add_argument('input_file', help='Input CSV file to anonymize')
    parser.add_argument('config_file', help='YAML configuration file')
    parser.add_argument('-o', '--output', help='Output CSV file (default: input_file_anonymized.csv)')
    parser.add_argument('--scores', action='store_true', help='Calculate and display anonymization scores')
    parser.add_argument('--report', action='store_true', help='Generate comprehensive HTML report')
    parser.add_argument('--report-dir', help='Directory for report output (required if --report is used)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logger(__name__)
    if args.verbose:
        logger.setLevel('DEBUG')
    
    try:
        # Check file existence
        if not Path(args.input_file).exists():
            logger.error(f"Input file not found: {args.input_file}")
            sys.exit(1)
        
        if not Path(args.config_file).exists():
            logger.error(f"Configuration file not found: {args.config_file}")
            sys.exit(1)
        
        # Process the data
        result = deidentify_from_file(
            args.input_file,
            args.config_file,
            args.output,
            return_scores=args.scores,
            generate_report=args.report,
            report_output_dir=args.report_dir
        )
        
        # Display results
        if isinstance(result, dict):
            print(f"\n✅ Anonymization completed successfully!")
            print(f"📁 Output file: {result['output_file']}")
            
            if 'scores' in result:
                scores = result['scores']
                print(f"\n📊 Anonymization Metrics:")
                print(f"   🔢 Anonify Score: {scores['anonify_score']:.2f}/100")
                print(f"   📋 Interpretation: {scores['score_interpretation']}")
                print(f"   📈 Columns Processed: {scores['total_columns']}")
            
            if 'report_path' in result:
                print(f"📄 Report generated: {result['report_path']}")
        else:
            print(f"\n✅ Anonymization completed successfully!")
            print(f"📁 Output file: {result}")
            
    except Exception as e:
        logger.error(f"Anonymization failed: {e}")
        sys.exit(1)


def generate_report_cli():
    """CLI entry point for report generation."""
    parser = argparse.ArgumentParser(
        description="Generate Anonify anonymization report from existing data",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('original_file', help='Original CSV file')
    parser.add_argument('anonymized_file', help='Anonymized CSV file')
    parser.add_argument('-c', '--config', help='YAML configuration file used for anonymization')
    parser.add_argument('-o', '--output-dir', help='Output directory for reports (required)')
    parser.add_argument('-f', '--formats', nargs='+', default=['html'], 
                       choices=['html', 'json', 'csv'], help='Report formats to generate')
    parser.add_argument('--name', help='Custom name for the report')
    
    args = parser.parse_args()
    
    logger = setup_logger(__name__)
    
    if not REPORTING_AVAILABLE:
        logger.error("Reporting functionality not available. Please install required dependencies.")
        sys.exit(1)
    
    try:
        # Read data files
        logger.info(f"Reading original data from {args.original_file}")
        original_df = pd.read_csv(args.original_file)
        
        logger.info(f"Reading anonymized data from {args.anonymized_file}")
        anonymized_df = pd.read_csv(args.anonymized_file)
        
        # Load config if provided
        config = None
        if args.config:
            with open(args.config, 'r') as f:
                config = yaml.safe_load(f)
        
        # Generate report
        reporter = AnonymizationReporter(output_dir=args.output_dir)
        output_paths = reporter.generate_comprehensive_report(
            original_df, 
            anonymized_df, 
            config,
            report_name=args.name,
            formats=args.formats
        )
        
        print("📄 Reports generated successfully:")
        for format_type, path in output_paths.items():
            print(f"   {format_type.upper()}: {path}")
            
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        sys.exit(1)


# Legacy support
def anonymize(dataframe: pd.DataFrame, yaml_config: Union[str, Dict[str, Any]]) -> pd.DataFrame:
    """
    Legacy function name for backwards compatibility.
    
    Args:
        dataframe: Input pandas DataFrame
        yaml_config: YAML configuration file path or config dict
        
    Returns:
        Anonymized DataFrame
    """
    return deidentify(dataframe, yaml_config)


if __name__ == '__main__':
    main()
