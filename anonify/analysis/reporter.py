"""
Report generator module for anonify package.

This module creates comprehensive reports combining scoring metrics and 
visualizations to assess anonymization effectiveness.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Union, Optional
import warnings
from io import StringIO

# Import anonify modules
from .scoring import AnonymizationScorer, quick_score
from .visualizer import AnonymizationVisualizer, create_quick_visualization

try:
    import plotly.io as pio
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

warnings.filterwarnings('ignore')


class AnonymizationReporter:
    """Main class for generating comprehensive anonymization reports."""
    
    def __init__(self, 
                 template: str = "plotly_white",
                 output_dir: str = "anonify_reports",
                 include_visualizations: bool = True):
        """
        Initialize reporter.
        
        Args:
            template: Plotly template for visualizations
            output_dir: Directory to save reports
            include_visualizations: Whether to include plotly visualizations
        """
        self.template = template
        self.output_dir = Path(output_dir)
        self.include_visualizations = include_visualizations and PLOTLY_AVAILABLE
        self.scorer = AnonymizationScorer()
        
        if self.include_visualizations:
            self.visualizer = AnonymizationVisualizer(template)
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_comprehensive_report(self,
                                    original_df: pd.DataFrame,
                                    anonymized_df: pd.DataFrame,
                                    config: Union[Dict[str, Any], None] = None,
                                    report_name: Union[str, None] = None,
                                    dataset_name: Union[str, None] = None,
                                    formats: List[str] = ['html', 'json']) -> Dict[str, str]:
        """
        Generate comprehensive anonymization report.
        
        Args:
            original_df: Original dataframe
            anonymized_df: Anonymized dataframe  
            config: Anonymization configuration used
            report_name: Name for the report files
            dataset_name: Name of the dataset to include in title
            formats: List of output formats ('html', 'json', 'pdf', 'csv')
            
        Returns:
            Dictionary mapping format to file path
        """
        if report_name is None:
            report_name = f"anonymization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Calculate scores
        scores = self.scorer.calculate_global_score(original_df, anonymized_df)
        
        # Generate visualizations if enabled
        figures = []
        if self.include_visualizations:
            figures = self.visualizer.create_comprehensive_report(
                original_df, anonymized_df, scores, max_columns=8
            )
        
        # Generate report data
        report_data = self._compile_report_data(
            original_df, anonymized_df, scores, config, figures
        )
        
        # Add dataset name to report data
        if dataset_name:
            report_data['dataset_name'] = dataset_name
        
        # Save in requested formats
        output_paths = {}
        for format_type in formats:
            if format_type == 'html':
                output_paths['html'] = self._generate_html_report(report_data, report_name)
            elif format_type == 'json':
                output_paths['json'] = self._generate_json_report(report_data, report_name)
            elif format_type == 'csv':
                output_paths['csv'] = self._generate_csv_report(report_data, report_name)
            elif format_type == 'pdf' and self.include_visualizations:
                output_paths['pdf'] = self._generate_pdf_report(report_data, report_name)
        
        return output_paths
    
    def _compile_report_data(self,
                           original_df: pd.DataFrame,
                           anonymized_df: pd.DataFrame,
                           scores: Dict[str, Any],
                           config: Union[Dict[str, Any], None],
                           figures: List) -> Dict[str, Any]:
        """Compile all report data into a structured format."""
        
        # Basic dataset info
        dataset_info = {
            'original_shape': original_df.shape,
            'anonymized_shape': anonymized_df.shape,
            'columns': list(original_df.columns),
            'total_records': len(original_df),
            'generation_time': datetime.now().isoformat(),
            'anonify_version': '0.1.0'
        }
        
        # Column analysis
        column_analysis = {}
        for col in original_df.columns:
            if col in anonymized_df.columns:
                col_type = self.scorer.detect_column_type(original_df[col])
                
                analysis = {
                    'type': col_type,
                    'original_unique': original_df[col].nunique(),
                    'anonymized_unique': anonymized_df[col].nunique(),
                    'original_nulls': original_df[col].isnull().sum(),
                    'anonymized_nulls': anonymized_df[col].isnull().sum(),
                    'distance_score': scores['column_scores'].get(col, 0),
                }
                
                # Add type-specific metrics
                if col_type == 'numerical':
                    analysis.update({
                        'original_mean': float(original_df[col].mean()) if original_df[col].notna().any() else None,
                        'anonymized_mean': float(anonymized_df[col].mean()) if anonymized_df[col].notna().any() else None,
                        'original_std': float(original_df[col].std()) if original_df[col].notna().any() else None,
                        'anonymized_std': float(anonymized_df[col].std()) if anonymized_df[col].notna().any() else None
                    })
                elif col_type == 'categorical':
                    orig_mode = original_df[col].mode()
                    anon_mode = anonymized_df[col].mode()
                    analysis.update({
                        'original_mode': orig_mode.iloc[0] if len(orig_mode) > 0 else None,
                        'anonymized_mode': anon_mode.iloc[0] if len(anon_mode) > 0 else None,
                        'value_overlap': len(set(original_df[col].dropna()) & set(anonymized_df[col].dropna()))
                    })
                
                column_analysis[col] = analysis
        
        # Configuration analysis
        config_analysis = {}
        if config and 'columns' in config:
            for col, col_config in config['columns'].items():
                methods_used = list(col_config.keys())
                config_analysis[col] = {
                    'methods': methods_used,
                    'configuration': col_config
                }
        
        # Risk assessment
        risk_assessment = self._assess_privacy_risk(scores, column_analysis)
        
        # Recommendations
        recommendations = self._generate_recommendations(scores, column_analysis, config_analysis)
        
        return {
            'dataset_info': dataset_info,
            'scores': scores,
            'column_analysis': column_analysis,
            'config_analysis': config_analysis,
            'risk_assessment': risk_assessment,
            'recommendations': recommendations,
            'figures': figures if self.include_visualizations else []
        }
    
    def _assess_privacy_risk(self, scores: Dict[str, Any], column_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess privacy risk based on scores and analysis."""
        
        risk_factors = []
        risk_level = "LOW"
        
        # Check overall score
        if scores['anonify_score'] < 40:
            risk_factors.append("Overall anonymization score is low")
            risk_level = "HIGH"
        elif scores['anonify_score'] < 60:
            risk_factors.append("Overall anonymization score is moderate")
            risk_level = "MEDIUM"
        
        # Check individual columns
        high_risk_columns = []
        for col, col_score in scores['column_scores'].items():
            if col_score < 0.3:  # Low anonymization for this column
                high_risk_columns.append(col)
                risk_factors.append(f"Column '{col}' has low anonymization score")
        
        if len(high_risk_columns) > len(scores['column_scores']) * 0.3:
            risk_level = "HIGH"
        elif len(high_risk_columns) > 0 and risk_level == "LOW":
            risk_level = "MEDIUM"
        
        # Check for potential re-identification risks
        reidentification_risks = []
        for col, analysis in column_analysis.items():
            if analysis['type'] == 'categorical' and analysis.get('value_overlap', 0) > analysis['original_unique'] * 0.8:
                reidentification_risks.append(f"Column '{col}' retains most original values")
        
        return {
            'overall_risk_level': risk_level,
            'risk_factors': risk_factors,
            'high_risk_columns': high_risk_columns,
            'reidentification_risks': reidentification_risks,
            'risk_score': 100 - scores['anonify_score']  # Inverse of anonymization score
        }
    
    def _generate_recommendations(self, 
                                scores: Dict[str, Any], 
                                column_analysis: Dict[str, Any],
                                config_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving anonymization."""
        
        recommendations = []
        
        # Overall score recommendations
        if scores['anonify_score'] < 40:
            recommendations.append("Consider applying stronger anonymization methods across more columns")
        elif scores['anonify_score'] < 60:
            recommendations.append("Good anonymization level achieved, consider fine-tuning for better privacy")
        
        # Column-specific recommendations
        for col, col_score in scores['column_scores'].items():
            if col_score < 0.3:
                col_info = column_analysis.get(col, {})
                col_type = col_info.get('type', 'unknown')
                
                if col_type == 'categorical' and col_info.get('value_overlap', 0) > col_info.get('original_unique', 0) * 0.5:
                    recommendations.append(f"Column '{col}': Consider using 'randomize' method instead of current method")
                elif col_type == 'numerical':
                    recommendations.append(f"Column '{col}': Consider adding noise or using 'obfuscate' method")
                elif col_type == 'text':
                    recommendations.append(f"Column '{col}': Consider using 'fake' method or 'hash' for better anonymization")
        
        # Configuration-based recommendations
        for col, config in config_analysis.items():
            if 'do_not_change' in config.get('methods', []):
                recommendations.append(f"Column '{col}': Currently unchanged - verify if this is intentional for privacy compliance")
        
        # General recommendations
        if len([s for s in scores['column_scores'].values() if s > 0.8]) < len(scores['column_scores']) * 0.5:
            recommendations.append("Consider applying anonymization to more columns for comprehensive privacy protection")
        
        return recommendations
    
    def _get_score_interpretation(self, score: float) -> str:
        """Get human-readable interpretation of anonymization score."""
        if score >= 81:
            return "Very High Anonymization - Maximum privacy protection"
        elif score >= 61:
            return "High Anonymization - Strong privacy protection"
        elif score >= 41:
            return "Medium Anonymization - Moderate privacy protection"
        elif score >= 21:
            return "Low Anonymization - Limited privacy protection"
        else:
            return "Very Low Anonymization - Minimal privacy protection"
    
    def _generate_html_report(self, report_data: Dict[str, Any], report_name: str) -> str:
        """Generate HTML report with clean, minimal Apple-inspired design."""
        
        # Get only the relevant score interpretation
        score = report_data['scores']['anonify_score']
        current_interpretation = self._get_score_interpretation(score)
        
        # Determine score color and category using proper Apple semantic colors
        if score >= 81:
            score_category = "very-high"
            score_color = "#30D158"  # systemGreen (proper Apple green)
            score_icon = "fas fa-shield-check"
            score_bg_alpha = "rgba(48, 209, 88, 0.1)"
        elif score >= 61:
            score_category = "high" 
            score_color = "#007AFF"  # systemBlue (Apple's primary blue)
            score_icon = "fas fa-check-circle"
            score_bg_alpha = "rgba(0, 122, 255, 0.1)"
        elif score >= 41:
            score_category = "medium"
            score_color = "#FF9500"  # systemOrange (Apple's orange)
            score_icon = "fas fa-exclamation-circle"
            score_bg_alpha = "rgba(255, 149, 0, 0.1)"
        elif score >= 21:
            score_category = "low"
            score_color = "#FF9500"  # systemOrange 
            score_icon = "fas fa-minus-circle"
            score_bg_alpha = "rgba(255, 149, 0, 0.1)"
        else:
            score_category = "very-low"
            score_color = "#FF3B30"  # systemRed (Apple's red)
            score_icon = "fas fa-exclamation-triangle"
            score_bg_alpha = "rgba(255, 59, 48, 0.1)"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Anonify Report{' - ' + report_data.get('dataset_name', '') if report_data.get('dataset_name') else ''}</title>
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
            <style>
                * {{ 
                    margin: 0; 
                    padding: 0; 
                    box-sizing: border-box; 
                }}
                
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
                    background: #f5f5f7;
                    color: #1d1d1f;
                    line-height: 1.47059;
                    font-weight: 400;
                    letter-spacing: -0.022em;
                }}
                
                .container {{ 
                    max-width: calc(100% - 80px); 
                    margin: 40px auto; 
                    background: #ffffff; 
                    border-radius: 18px; 
                    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04), 0 8px 32px rgba(0, 0, 0, 0.04);
                    overflow: hidden;
                    border: 1px solid rgba(0, 0, 0, 0.05);
                }}
                
                .header {{ 
                    text-align: center; 
                    padding: 48px 32px 32px;
                    background: #ffffff;
                }}
                
                .header h1 {{ 
                    font-size: 40px; 
                    font-weight: 600; 
                    color: #1d1d1f;
                    margin-bottom: 8px;
                    letter-spacing: -0.5px;
                    line-height: 1.1;
                }}
                
                .header .subtitle {{ 
                    font-size: 19px; 
                    color: #6e6e73; 
                    font-weight: 400;
                    letter-spacing: 0.012em;
                }}
                
                .score-section {{ 
                    text-align: center; 
                    padding: 32px; 
                    background: #fafafa;
                    border-bottom: 1px solid rgba(0, 0, 0, 0.08);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 32px;
                    flex-wrap: wrap;
                }}
                
                .score-circle {{ 
                    width: 80px; 
                    height: 80px; 
                    border-radius: 50%; 
                    background: {score_color}; 
                    display: flex; 
                    align-items: center; 
                    justify-content: center; 
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                    flex-shrink: 0;
                }}
                
                .score-circle .score {{ 
                    font-size: 28px; 
                    font-weight: 600; 
                    color: white; 
                    letter-spacing: -0.5px;
                }}
                
                .score-content {{
                    flex: 1;
                    max-width: 600px;
                    text-align: left;
                }}
                
                .score-label {{ 
                    font-size: 14px; 
                    color: #6e6e73; 
                    margin-bottom: 8px;
                    font-weight: 500;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                
                .interpretation {{ 
                    background: {score_bg_alpha};
                    padding: 20px 24px; 
                    border-radius: 12px; 
                    border: 1px solid rgba(0, 0, 0, 0.04);
                }}
                
                .interpretation h3 {{ 
                    color: {score_color};
                    font-size: 20px; 
                    font-weight: 600; 
                    margin-bottom: 8px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    letter-spacing: -0.3px;
                }}
                
                .interpretation p {{ 
                    color: #1d1d1f; 
                    font-size: 16px; 
                    line-height: 1.4;
                    letter-spacing: 0.012em;
                    margin: 0;
                }}
                
                .content {{ 
                    padding: 48px 32px;
                    background: #ffffff;
                }}
                
                .section {{ 
                    margin: 48px 0;
                }}
                
                .section h2 {{ 
                    font-size: 32px; 
                    font-weight: 600; 
                    color: #1d1d1f; 
                    margin-bottom: 24px;
                    letter-spacing: -0.5px;
                    line-height: 1.125;
                }}
                
                .summary-grid {{ 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); 
                    gap: 24px; 
                    margin: 32px 0;
                }}
                
                .summary-card {{ 
                    text-align: center; 
                    padding: 32px 24px; 
                    background: #fafafa; 
                    border-radius: 16px; 
                    border: 1px solid rgba(0, 0, 0, 0.05);
                }}
                
                .summary-card .value {{ 
                    font-size: 40px; 
                    font-weight: 600; 
                    color: #1d1d1f; 
                    margin-bottom: 8px;
                    letter-spacing: -0.5px;
                }}
                
                .summary-card .label {{ 
                    font-size: 17px; 
                    color: #6e6e73; 
                    font-weight: 400;
                    letter-spacing: 0.012em;
                }}
                
                .summary-card.risk {{ 
                    background: {score_bg_alpha};
                    border-color: {score_color}33;
                }}
                
                .summary-card.risk .value {{ 
                    color: {score_color};
                }}
                
                table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                    background: #ffffff; 
                    border-radius: 12px; 
                    overflow: hidden;
                    border: 1px solid rgba(0, 0, 0, 0.08);
                    margin: 24px 0;
                }}
                
                th {{ 
                    background: #fafafa; 
                    padding: 20px 16px; 
                    text-align: left; 
                    font-size: 17px; 
                    font-weight: 600; 
                    color: #1d1d1f;
                    border-bottom: 1px solid rgba(0, 0, 0, 0.08);
                    letter-spacing: -0.022em;
                }}
                
                td {{ 
                    padding: 20px 16px; 
                    font-size: 17px; 
                    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
                    letter-spacing: -0.022em;
                }}
                
                tr:last-child td {{ 
                    border-bottom: none; 
                }}
                
                .risk-low {{ color: #30D158; font-weight: 600; }}
                .risk-medium {{ color: #FF9500; font-weight: 600; }}
                .risk-high {{ color: #FF3B30; font-weight: 600; }}
                
                .recommendations {{ 
                    background: #fafafa; 
                    padding: 32px; 
                    border-radius: 16px; 
                    margin: 32px 0;
                    border: 1px solid rgba(0, 0, 0, 0.05);
                }}
                
                .recommendations h3 {{ 
                    color: #1d1d1f; 
                    font-size: 24px; 
                    font-weight: 600; 
                    margin-bottom: 20px;
                    letter-spacing: -0.3px;
                }}
                
                .recommendations ul {{ 
                    list-style: none; 
                    padding: 0; 
                }}
                
                .recommendations li {{ 
                    padding: 12px 0; 
                    font-size: 17px; 
                    color: #1d1d1f;
                    position: relative;
                    padding-left: 32px;
                    line-height: 1.4211;
                    letter-spacing: -0.022em;
                }}
                
                .recommendations li::before {{ 
                    content: '•'; 
                    color: #007AFF; 
                    font-size: 24px; 
                    position: absolute;
                    left: 0;
                    top: 8px;
                    font-weight: 600;
                }}
                
                .visualizations {{ 
                    margin: 48px 0;
                }}
                
                .viz-container {{ 
                    background: #ffffff; 
                    border-radius: 16px; 
                    padding: 32px 40px; 
                    border: 1px solid rgba(0, 0, 0, 0.05);
                    margin: 24px 0;
                }}
                
                .viz-container h3 {{ 
                    font-size: 24px; 
                    font-weight: 600; 
                    color: #1d1d1f; 
                    margin-bottom: 24px;
                    letter-spacing: -0.3px;
                }}
                
                .column-selector {{ 
                    text-align: center; 
                    margin: 32px 0; 
                }}
                
                .column-selector select, .apple-select {{ 
                    padding: 16px 20px; 
                    font-size: 17px; 
                    border: 2px solid rgba(0, 0, 0, 0.1); 
                    border-radius: 12px; 
                    background: #ffffff; 
                    color: #1d1d1f; 
                    min-width: 320px; 
                    font-family: inherit;
                    letter-spacing: -0.022em;
                    font-weight: 400;
                    appearance: none;
                    background-image: url("data:image/svg+xml;charset=UTF-8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%236e6e73' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6,9 12,15 18,9'%3E%3C/polyline%3E%3C/svg%3E");
                    background-repeat: no-repeat;
                    background-position: right 16px center;
                    background-size: 16px;
                    padding-right: 48px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }}
                
                .column-selector select:hover, .apple-select:hover {{ 
                    border-color: rgba(0, 0, 0, 0.2);
                    background-color: #fafafa;
                }}
                
                .column-selector select:focus, .apple-select:focus {{ 
                    outline: none; 
                    border-color: #007AFF; 
                    box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.1);
                    background-color: #ffffff;
                }}
                
                .column-chart {{ 
                    display: none; 
                }}
                
                .column-chart.active {{ 
                    display: block; 
                }}
                
                @media (max-width: 768px) {{ 
                    .container {{ 
                        margin: 20px; 
                        border-radius: 16px; 
                    }}
                    
                    .header, .content {{ 
                        padding: 32px 20px; 
                    }}
                    
                    .score-section {{ 
                        padding: 24px 20px;
                        flex-direction: column;
                        gap: 20px;
                    }}
                    
                    .score-content {{
                        text-align: center;
                    }}
                    
                    .header h1 {{ 
                        font-size: 32px; 
                    }}
                    
                    .summary-grid {{
                        grid-template-columns: 1fr; 
                        gap: 16px;
                    }}
                    
                    .column-selector select {{ 
                        min-width: 240px; 
                    }}
                    
                    .score-circle {{
                        width: 70px;
                        height: 70px;
                    }}
                    
                    .score-circle .score {{
                        font-size: 24px;
                    }}
                }}
            </style>
        """
        
        if self.include_visualizations:
            html_content += """
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <script>
                function showColumnChart(columnName) {
                    const allCharts = document.querySelectorAll('.column-chart');
                    allCharts.forEach(chart => chart.classList.remove('active'));
                    
                    if (columnName && columnName !== 'overview') {
                        const selectedChart = document.getElementById('chart_' + columnName);
                        if (selectedChart) {
                            selectedChart.classList.add('active');
                        }
                    }
                }
            </script>
            """
        
        html_content += f"""
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Anonymization Report{' - ' + report_data.get('dataset_name', '') if report_data.get('dataset_name') else ''}</h1>
                    <div class="subtitle">Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</div>
                </div>
                
                <div class="score-section">
                    <div class="score-circle">
                        <div class="score">{report_data['scores']['anonify_score']:.0f}</div>
                    </div>
                    <div class="score-content">
                        <div class="score-label">Anonymization Score</div>
                        <div class="interpretation">
                            <h3>
                                <i class="{score_icon}"></i>
                                {current_interpretation}
                            </h3>
                            <p>"""
        
        # Add specific interpretation based on score
        if score >= 81:
            html_content += "Excellent anonymization with minimal re-identification risk. Safe for public sharing and compliance with strict privacy regulations."
        elif score >= 61:
            html_content += "Good anonymization while maintaining data utility. Suitable for most sharing scenarios including research and analytics."
        elif score >= 41:
            html_content += "Reasonable anonymization with some utility preserved. Suitable for internal analysis but consider additional protection for external sharing."
        elif score >= 21:
            html_content += "Some changes made but original data relationships remain visible. Use caution when sharing this data."
        else:
            html_content += "Data is largely unchanged. Original patterns and values are easily identifiable. Not suitable for sharing or analysis of sensitive data."
        
        html_content += f"""</p>
                        </div>
                    </div>
                </div>
                
                <div class="content">
                    <div class="section">
                        <h2>Executive Summary</h2>
                        <div class="summary-grid">
                            <div class="summary-card">
                                <div class="value">{report_data['dataset_info']['total_records']:,}</div>
                                <div class="label">Total Records</div>
                            </div>
                            <div class="summary-card">
                                <div class="value">{len(report_data['dataset_info']['columns'])}</div>
                                <div class="label">Columns Analyzed</div>
                            </div>
                            <div class="summary-card risk">
                                <div class="value">{report_data['risk_assessment']['overall_risk_level']}</div>
                                <div class="label">Privacy Risk</div>
                            </div>
                        </div>
                        <p><strong>Interpretation:</strong> {current_interpretation}</p>
                    </div>
        """
        
        # Add visualizations if available
        if self.include_visualizations and report_data['figures']:
            html_content += '<div class="visualizations"><h2>Interactive Visualizations</h2>'
            
            figures = report_data['figures']
            score_chart = figures[0] if figures else None
            column_charts = figures[1:] if len(figures) > 1 else []
            
            if score_chart:
                score_chart_div = pio.to_html(score_chart, include_plotlyjs=False, div_id="overview_chart")
                html_content += f'''
                <div class="viz-container">
                    <h3>Column Analysis</h3>
                    <div class="chart-container">{score_chart_div}</div>
                </div>
                '''
            
            html_content += '</div>'
        
        html_content += f"""
                    <div class="section">
                        <h2>Column Analysis</h2>
                        <table>
                            <thead>
                                <tr>
                                    <th>Column</th>
                                    <th>Type</th>
                                    <th>Score</th>
                                    <th>Original Values</th>
                                    <th>Anonymized Values</th>
                                    <th>Risk</th>
                                </tr>
                            </thead>
                            <tbody>
        """
        
        for col, analysis in report_data['column_analysis'].items():
            risk_class = "risk-high" if analysis['distance_score'] < 0.3 else ("risk-medium" if analysis['distance_score'] < 0.6 else "risk-low")
            risk_text = "High" if analysis['distance_score'] < 0.3 else ("Medium" if analysis['distance_score'] < 0.6 else "Low")
            
            html_content += f"""
                                <tr>
                                    <td>{col}</td>
                                    <td>{analysis['type'].title()}</td>
                                    <td>{analysis['distance_score']:.3f}</td>
                                    <td>{analysis['original_unique']}</td>
                                    <td>{analysis['anonymized_unique']}</td>
                                    <td class="{risk_class}">{risk_text}</td>
                                </tr>
            """
        
        html_content += """
                            </tbody>
                        </table>
                    </div>
        """
        
        if report_data['recommendations']:
            html_content += f"""
                    <div class="section">
                        <div class="recommendations">
                            <h3>Recommendations</h3>
                            <ul>
            """
            
            for rec in report_data['recommendations']:
                html_content += f"<li>{rec}</li>"
            
            html_content += """
                            </ul>
                        </div>
                    </div>
            """
        
        # Add column-specific analysis at the bottom
        # TODO: Uncomment when column-specific analysis is needed
        # if self.include_visualizations and report_data['figures']:
        #     figures = report_data['figures']
        #     column_charts = figures[1:] if len(figures) > 1 else []
        #     
        #     if column_charts:
        #         html_content += '''
        #         <div class="section">
        #             <h2>Column-Specific Analysis</h2>
        #             <div class="column-selector">
        #                 <select onchange="showColumnChart(this.value)" class="apple-select">
        #                     <option value="overview">Select a column to analyze in detail</option>
        #         '''
        #         
        #         # Show ALL columns, not just ones with charts
        #         for col_name in report_data['column_analysis'].keys():
        #             html_content += f'<option value="{col_name}">{col_name}</option>'
        #         
        #         html_content += '</select></div>'
        #         
        #         for i, fig in enumerate(column_charts):
        #             chart_title = fig.layout.title.text if fig.layout.title else f"Chart {i+1}"
        #             if ": " in chart_title:
        #                 column_name = chart_title.split(": ")[-1]
        #             else:
        #                 column_name = f"column_{i+1}"
        #             
        #             chart_div = pio.to_html(fig, include_plotlyjs=False, div_id=f"chart_{column_name}_content")
        #             html_content += f'''
        #             <div id="chart_{column_name}" class="column-chart">
        #                 <div class="chart-container">{chart_div}</div>
        #             </div>
        #             '''
        #         
        #         html_content += '</div>'
        
        html_content += """
                </div>
            </div>
        </body>
        </html>
        """
        
        # Save HTML file
        html_path = self.output_dir / f"{report_name}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(html_path)
    
    def _generate_json_report(self, report_data: Dict[str, Any], report_name: str) -> str:
        """Generate JSON report."""
        
        # Remove figures from JSON (not serializable)
        json_data = report_data.copy()
        json_data.pop('figures', None)
        
        # Convert numpy types to native Python types
        def convert_numpy(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            else:
                return obj
        
        json_data = convert_numpy(json_data)
        
        json_path = self.output_dir / f"{report_name}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        return str(json_path)
    
    def _generate_csv_report(self, report_data: Dict[str, Any], report_name: str) -> str:
        """Generate CSV summary report."""
        
        # Create summary DataFrame
        summary_data = []
        for col, analysis in report_data['column_analysis'].items():
            summary_data.append({
                'column': col,
                'type': analysis['type'],
                'distance_score': analysis['distance_score'],
                'original_unique': analysis['original_unique'],
                'anonymized_unique': analysis['anonymized_unique'],
                'original_nulls': analysis['original_nulls'],
                'anonymized_nulls': analysis['anonymized_nulls']
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        csv_path = self.output_dir / f"{report_name}.csv"
        summary_df.to_csv(csv_path, index=False)
        
        return str(csv_path)
    
    def _generate_pdf_report(self, report_data: Dict[str, Any], report_name: str) -> str:
        """Generate PDF report (requires additional dependencies)."""
        # This would require additional dependencies like reportlab or weasyprint
        # For now, return empty string to indicate PDF generation is not available
        return ""


def generate_quick_report(original_df: pd.DataFrame, 
                        anonymized_df: pd.DataFrame,
                        config: Union[Dict[str, Any], None] = None,
                        dataset_name: Union[str, None] = None,
                        output_dir: str = "anonify_reports") -> str:
    """
    Generate a quick anonymization report.
    
    Args:
        original_df: Original dataframe
        anonymized_df: Anonymized dataframe
        config: Anonymization configuration used
        dataset_name: Name of the dataset to include in title
        output_dir: Directory to save report
        
    Returns:
        Path to generated HTML report
    """
    reporter = AnonymizationReporter(output_dir=output_dir)
    outputs = reporter.generate_comprehensive_report(
        original_df, anonymized_df, config, 
        dataset_name=dataset_name,
        formats=['html']
    )
    return outputs.get('html', '') 