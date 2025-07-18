"""
Visualization module for anonify package.

This module provides comprehensive visualization capabilities for comparing
original and anonymized datasets using plotly.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from typing import Dict, List, Tuple, Union, Any, Optional
import warnings

warnings.filterwarnings('ignore')


class AnonymizationVisualizer:
    """Main class for creating anonymization comparison visualizations."""
    
    def __init__(self, template: str = "plotly_white"):
        """
        Initialize visualizer with plotly template.
        
        Args:
            template: Plotly template to use for styling
        """
        self.template = template
        self.colors = {
            'original': px.colors.qualitative.Set2[0],  # Matter palette alternative
            'anonymized': px.colors.qualitative.Set2[1], # Matter palette alternative
            'background': '#f8f9fa',
            'text': '#2c3e50'
        }
        
    def _detect_column_type(self, series: pd.Series) -> str:
        """Detect column type for appropriate visualization."""
        series_clean = series.dropna()
        
        if len(series_clean) == 0:
            return 'categorical'
        
        # Check if numerical
        try:
            pd.to_numeric(series_clean)
            return 'numerical'
        except (ValueError, TypeError):
            pass
        
        # Check if datetime
        try:
            pd.to_datetime(series_clean)
            return 'datetime'
        except (ValueError, TypeError):
            pass
        
        # Check if categorical
        unique_ratio = len(series_clean.unique()) / len(series_clean)
        if unique_ratio < 0.5:
            return 'categorical'
        else:
            return 'text'
    
    def create_distribution_comparison(self, original: pd.Series, anonymized: pd.Series, 
                                     column_name: str, show_stats: bool = True) -> go.Figure:
        """
        Create distribution comparison plot based on column type.
        
        Args:
            original: Original column data
            anonymized: Anonymized column data
            column_name: Name of the column
            show_stats: Whether to show statistical information
            
        Returns:
            Plotly figure object
        """
        column_type = self._detect_column_type(original)
        
        if column_type == 'numerical':
            return self._create_numerical_distribution(original, anonymized, column_name, show_stats)
        elif column_type == 'categorical':
            return self._create_categorical_distribution(original, anonymized, column_name, show_stats)
        elif column_type == 'datetime':
            return self._create_datetime_distribution(original, anonymized, column_name, show_stats)
        else:  # text
            return self._create_text_distribution(original, anonymized, column_name, show_stats)
    
    def _create_numerical_distribution(self, original: pd.Series, anonymized: pd.Series, 
                                     column_name: str, show_stats: bool) -> go.Figure:
        """Create numerical distribution comparison."""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Distribution Comparison', 'Box Plots', 'Q-Q Plot', 'Statistics'),
            specs=[[{"colspan": 2}, None],
                   [{"type": "box"}, {"type": "table"}]]
        )
        
        # Distribution comparison (histograms)
        fig.add_trace(
            go.Histogram(
                x=original.dropna(),
                name='Original',
                opacity=0.7,
                marker_color=self.colors['original'],
                nbinsx=30
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Histogram(
                x=anonymized.dropna(),
                name='Anonymized',
                opacity=0.7,
                marker_color=self.colors['anonymized'],
                nbinsx=30
            ),
            row=1, col=1
        )
        
        # Box plots
        fig.add_trace(
            go.Box(
                y=original.dropna(),
                name='Original',
                marker_color=self.colors['original']
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Box(
                y=anonymized.dropna(),
                name='Anonymized',
                marker_color=self.colors['anonymized']
            ),
            row=2, col=1
        )
        
        # Statistics table
        if show_stats:
            orig_stats = original.describe()
            anon_stats = anonymized.describe()
            
            stats_table = go.Table(
                header=dict(values=['Statistic', 'Original', 'Anonymized']),
                cells=dict(values=[
                    ['Mean', 'Std', 'Min', 'Max', 'Median'],
                    [f"{orig_stats['mean']:.3f}", f"{orig_stats['std']:.3f}", 
                     f"{orig_stats['min']:.3f}", f"{orig_stats['max']:.3f}", 
                     f"{orig_stats['50%']:.3f}"],
                    [f"{anon_stats['mean']:.3f}", f"{anon_stats['std']:.3f}", 
                     f"{anon_stats['min']:.3f}", f"{anon_stats['max']:.3f}", 
                     f"{anon_stats['50%']:.3f}"]
                ])
            )
            fig.add_trace(stats_table, row=2, col=2)
        
        fig.update_layout(
            title=f"Numerical Distribution Analysis: {column_name}",
            template=self.template,
            height=600
        )
        
        return fig
    
    def _create_categorical_distribution(self, original: pd.Series, anonymized: pd.Series, 
                                       column_name: str, show_stats: bool) -> go.Figure:
        """Create categorical distribution comparison."""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Original Distribution', 'Anonymized Distribution', 
                          'Value Overlap', 'Category Statistics'),
            specs=[[{"type": "pie"}, {"type": "pie"}], 
                   [{"type": "bar"}, {"type": "table"}]]
        )
        
        # Original pie chart
        orig_counts = original.value_counts().head(10)  # Top 10 categories
        fig.add_trace(
            go.Pie(
                labels=orig_counts.index,
                values=orig_counts.values,
                name="Original",
                marker_colors=px.colors.qualitative.Set3
            ),
            row=1, col=1
        )
        
        # Anonymized pie chart
        anon_counts = anonymized.value_counts().head(10)
        fig.add_trace(
            go.Pie(
                labels=anon_counts.index,
                values=anon_counts.values,
                name="Anonymized",
                marker_colors=px.colors.qualitative.Pastel
            ),
            row=1, col=2
        )
        
        # Value overlap analysis
        orig_set = set(original.dropna().unique())
        anon_set = set(anonymized.dropna().unique())
        overlap = orig_set.intersection(anon_set)
        
        overlap_data = {
            'Category': ['Original Only', 'Shared', 'Anonymized Only'],
            'Count': [len(orig_set - anon_set), len(overlap), len(anon_set - orig_set)]
        }
        
        fig.add_trace(
            go.Bar(
                x=overlap_data['Category'],
                y=overlap_data['Count'],
                marker_color=[self.colors['original'], '#9467bd', self.colors['anonymized']]
            ),
            row=2, col=1
        )
        
        # Statistics table
        if show_stats:
            stats_table = go.Table(
                header=dict(values=['Metric', 'Original', 'Anonymized']),
                cells=dict(values=[
                    ['Unique Values', 'Most Common', 'Mode Frequency'],
                    [str(original.nunique()), str(original.mode().iloc[0] if len(original.mode()) > 0 else 'N/A'), 
                     str(orig_counts.iloc[0] if len(orig_counts) > 0 else 0)],
                    [str(anonymized.nunique()), str(anonymized.mode().iloc[0] if len(anonymized.mode()) > 0 else 'N/A'), 
                     str(anon_counts.iloc[0] if len(anon_counts) > 0 else 0)]
                ])
            )
            fig.add_trace(stats_table, row=2, col=2)
        
        fig.update_layout(
            title=f"Categorical Distribution Analysis: {column_name}",
            template=self.template,
            height=600
        )
        
        return fig
    
    def _create_datetime_distribution(self, original: pd.Series, anonymized: pd.Series, 
                                    column_name: str, show_stats: bool) -> go.Figure:
        """Create datetime distribution comparison."""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Time Series Distribution', 'Date Range Comparison', 
                          'Monthly Distribution', 'Statistics'),
            specs=[[{"type": "scatter"}, {"type": "bar"}], 
                   [{"type": "bar"}, {"type": "table"}]]
        )
        
        # Convert to datetime
        orig_dt = pd.to_datetime(original.dropna())
        anon_dt = pd.to_datetime(anonymized.dropna())
        
        # Time series scatter
        fig.add_trace(
            go.Scatter(
                x=list(range(len(orig_dt))),
                y=orig_dt,
                mode='markers',
                name='Original',
                marker_color=self.colors['original']
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=list(range(len(anon_dt))),
                y=anon_dt,
                mode='markers',
                name='Anonymized',
                marker_color=self.colors['anonymized']
            ),
            row=1, col=1
        )
        
        # Date range comparison
        date_ranges = {
            'Dataset': ['Original', 'Anonymized'],
            'Min Date': [orig_dt.min(), anon_dt.min()],
            'Max Date': [orig_dt.max(), anon_dt.max()]
        }
        
        for i, dataset in enumerate(['Original', 'Anonymized']):
            fig.add_trace(
                go.Bar(
                    x=[date_ranges['Min Date'][i], date_ranges['Max Date'][i]],
                    y=[dataset, dataset],
                    orientation='h',
                    name=f"{dataset} Range",
                    marker_color=self.colors['original'] if i == 0 else self.colors['anonymized']
                ),
                row=1, col=2
            )
        
        # Monthly distribution
        orig_monthly = orig_dt.dt.month.value_counts().sort_index()
        anon_monthly = anon_dt.dt.month.value_counts().sort_index()
        
        fig.add_trace(
            go.Bar(
                x=orig_monthly.index,
                y=orig_monthly.values,
                name='Original Monthly',
                marker_color=self.colors['original'],
                opacity=0.7
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=anon_monthly.index,
                y=anon_monthly.values,
                name='Anonymized Monthly',
                marker_color=self.colors['anonymized'],
                opacity=0.7
            ),
            row=2, col=1
        )
        
        # Statistics table
        if show_stats:
            stats_table = go.Table(
                header=dict(values=['Metric', 'Original', 'Anonymized']),
                cells=dict(values=[
                    ['Min Date', 'Max Date', 'Date Range (days)'],
                    [str(orig_dt.min().date()), str(orig_dt.max().date()), 
                     str((orig_dt.max() - orig_dt.min()).days)],
                    [str(anon_dt.min().date()), str(anon_dt.max().date()), 
                     str((anon_dt.max() - anon_dt.min()).days)]
                ])
            )
            fig.add_trace(stats_table, row=2, col=2)
        
        fig.update_layout(
            title=f"DateTime Distribution Analysis: {column_name}",
            template=self.template,
            height=600
        )
        
        return fig
    
    def _create_text_distribution(self, original: pd.Series, anonymized: pd.Series, 
                                column_name: str, show_stats: bool) -> go.Figure:
        """Create text distribution comparison."""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('String Length Distribution', 'Character Analysis', 
                          'Word Count Distribution', 'Text Statistics'),
            specs=[[{"type": "scatter"}, {"type": "bar"}], 
                   [{"type": "histogram"}, {"type": "table"}]]
        )
        
        # String length comparison
        orig_lengths = original.dropna().astype(str).str.len()
        anon_lengths = anonymized.dropna().astype(str).str.len()
        
        fig.add_trace(
            go.Scatter(
                x=list(range(len(orig_lengths))),
                y=orig_lengths,
                mode='markers',
                name='Original Lengths',
                marker_color=self.colors['original']
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=list(range(len(anon_lengths))),
                y=anon_lengths,
                mode='markers',
                name='Anonymized Lengths',
                marker_color=self.colors['anonymized']
            ),
            row=1, col=1
        )
        
        # Character type analysis
        orig_str = original.dropna().astype(str)
        anon_str = anonymized.dropna().astype(str)
        
        char_analysis = {
            'Type': ['Alphabetic', 'Numeric', 'Special'],
            'Original': [
                orig_str.str.contains('[a-zA-Z]').sum(),
                orig_str.str.contains('[0-9]').sum(),
                orig_str.str.contains('[^a-zA-Z0-9\s]').sum()
            ],
            'Anonymized': [
                anon_str.str.contains('[a-zA-Z]').sum(),
                anon_str.str.contains('[0-9]').sum(),
                anon_str.str.contains('[^a-zA-Z0-9\s]').sum()
            ]
        }
        
        fig.add_trace(
            go.Bar(
                x=char_analysis['Type'],
                y=char_analysis['Original'],
                name='Original',
                marker_color=self.colors['original'],
                opacity=0.7
            ),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Bar(
                x=char_analysis['Type'],
                y=char_analysis['Anonymized'],
                name='Anonymized',
                marker_color=self.colors['anonymized'],
                opacity=0.7
            ),
            row=1, col=2
        )
        
        # Word count distribution
        orig_words = orig_str.str.split().str.len()
        anon_words = anon_str.str.split().str.len()
        
        fig.add_trace(
            go.Histogram(
                x=orig_words,
                name='Original Word Count',
                marker_color=self.colors['original'],
                opacity=0.7
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Histogram(
                x=anon_words,
                name='Anonymized Word Count',
                marker_color=self.colors['anonymized'],
                opacity=0.7
            ),
            row=2, col=1
        )
        
        # Statistics table
        if show_stats:
            stats_table = go.Table(
                header=dict(values=['Metric', 'Original', 'Anonymized']),
                cells=dict(values=[
                    ['Avg Length', 'Unique Values', 'Avg Word Count'],
                    [f"{orig_lengths.mean():.2f}", str(original.nunique()), 
                     f"{orig_words.mean():.2f}"],
                    [f"{anon_lengths.mean():.2f}", str(anonymized.nunique()), 
                     f"{anon_words.mean():.2f}"]
                ])
            )
            fig.add_trace(stats_table, row=2, col=2)
        
        fig.update_layout(
            title=f"Text Distribution Analysis: {column_name}",
            template=self.template,
            height=600
        )
        
        return fig
    
    def create_score_visualization(self, scores: Dict[str, Any]) -> go.Figure:
        """
        Create clean visualization for anonymization scores.
        
        Args:
            scores: Dictionary containing scoring results
            
        Returns:
            Plotly figure with score visualization
        """
        # Column scores bar chart with matter colors mapped to score values
        column_names = list(scores['column_scores'].keys())
        column_scores = list(scores['column_scores'].values())
        
        fig = go.Figure()
        
        fig.add_trace(
            go.Bar(
                x=column_names,
                y=column_scores,
                marker=dict(
                    color=column_scores,  # Map colors to actual score values
                    colorscale='matter',  # Use matter color scale
                    cmin=0,  # Minimum value for color scale
                    cmax=1,  # Maximum value for color scale
                    colorbar=dict(
                        title=dict(
                            text="Anonymization Score",
                            side="right"
                        ),
                        thickness=15,
                        len=0.7,
                        x=1.02
                    )
                ),
                showlegend=False,
                hovertemplate="<b>%{x}</b><br>Score: %{y:.3f}<extra></extra>"
            )
        )
        
        fig.update_layout(
            title="Column Analysis",
            template=self.template,
            height=500,
            showlegend=False,
            margin=dict(l=40, r=40, t=80, b=100),  # Small indent left/right, more space for labels
            xaxis_title="Columns",
            yaxis_title="Anonymization Score"
        )
        
        # Update x-axis for column scores to rotate labels if needed
        fig.update_xaxes(tickangle=45)
        
        return fig
    
    def create_comprehensive_report(self, original_df: pd.DataFrame, 
                                  anonymized_df: pd.DataFrame, 
                                  scores: Dict[str, Any],
                                  max_columns: int = 6) -> List[go.Figure]:
        """
        Create comprehensive visualization report.
        
        Args:
            original_df: Original dataframe
            anonymized_df: Anonymized dataframe
            scores: Scoring results
            max_columns: Maximum number of columns to visualize individually
            
        Returns:
            List of plotly figures
        """
        figures = []
        
        # Add score visualization
        figures.append(self.create_score_visualization(scores))
        
        # Add column-wise comparisons for top columns by score
        column_scores = scores['column_scores']
        top_columns = sorted(column_scores.items(), key=lambda x: x[1], reverse=True)[:max_columns]
        
        for column_name, _ in top_columns:
            if column_name in original_df.columns and column_name in anonymized_df.columns:
                fig = self.create_distribution_comparison(
                    original_df[column_name],
                    anonymized_df[column_name],
                    column_name
                )
                figures.append(fig)
        
        return figures


def create_quick_visualization(original_df: pd.DataFrame, anonymized_df: pd.DataFrame, 
                             scores: Dict[str, Any]) -> go.Figure:
    """
    Create a quick summary visualization.
    
    Args:
        original_df: Original dataframe
        anonymized_df: Anonymized dataframe
        scores: Scoring results
        
    Returns:
        Single plotly figure with summary
    """
    visualizer = AnonymizationVisualizer()
    return visualizer.create_score_visualization(scores) 