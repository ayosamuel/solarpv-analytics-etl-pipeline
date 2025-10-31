"""
Core plotting utilities for solar analytics visualization
"""

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any
from dataclasses import dataclass
import warnings

# Set plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")
warnings.filterwarnings('ignore')


@dataclass
class PlotConfig:
    """Configuration for plot styling and layout"""
    figure_size: Tuple[int, int] = (12, 8)
    dpi: int = 300
    color_palette: str = 'husl'
    style: str = 'seaborn-v0_8'
    interactive: bool = True


class PerformancePlotter:
    """Visualization tools for performance ratio results"""
    
    def __init__(self, config: PlotConfig = None):
        self.config = config or PlotConfig()
        
    def plot_pr_timeseries(self, pr_results, show_temp_corrected: bool = True):
        """Plot PR time series with optional temperature correction"""
        
        if self.config.interactive:
            return self._plot_pr_timeseries_plotly(pr_results, show_temp_corrected)
        else:
            return self._plot_pr_timeseries_matplotlib(pr_results, show_temp_corrected)
    
    def _plot_pr_timeseries_plotly(self, pr_results, show_temp_corrected):
        """Interactive PR time series using Plotly"""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Daily Performance Ratio', 'Monthly Average PR'),
            shared_xaxes=True,
            vertical_spacing=0.1
        )
        
        # Daily PR
        if hasattr(pr_results, 'pr_daily') and pr_results.pr_daily is not None:
            fig.add_trace(
                go.Scatter(
                    x=pr_results.pr_daily.index,
                    y=pr_results.pr_daily.iloc[:, 0],  # First column assumed to be main PR
                    mode='lines+markers',
                    name='Daily PR',
                    line=dict(color='blue', width=2),
                    marker=dict(size=4)
                ),
                row=1, col=1
            )
            
            if show_temp_corrected and hasattr(pr_results, 'pr_temp_corrected'):
                fig.add_trace(
                    go.Scatter(
                        x=pr_results.pr_temp_corrected.index,
                        y=pr_results.pr_temp_corrected.iloc[:, 0],
                        mode='lines+markers',
                        name='Temperature Corrected PR',
                        line=dict(color='red', width=2, dash='dash'),
                        marker=dict(size=4)
                    ),
                    row=1, col=1
                )
        
        # Monthly PR
        if hasattr(pr_results, 'pr_monthly') and pr_results.pr_monthly is not None:
            fig.add_trace(
                go.Bar(
                    x=pr_results.pr_monthly.index,
                    y=pr_results.pr_monthly.iloc[:, 0],
                    name='Monthly PR',
                    marker_color='lightblue'
                ),
                row=2, col=1
            )
        
        fig.update_layout(
            height=800,
            title_text="Performance Ratio Analysis",
            showlegend=True
        )
        
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Performance Ratio", row=1, col=1)
        fig.update_yaxes(title_text="Performance Ratio", row=2, col=1)
        
        return fig
    
    def _plot_pr_timeseries_matplotlib(self, pr_results, show_temp_corrected):
        """Static PR time series using Matplotlib"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.config.figure_size, 
                                       dpi=self.config.dpi)
        
        # Daily PR
        if hasattr(pr_results, 'pr_daily') and pr_results.pr_daily is not None:
            ax1.plot(pr_results.pr_daily.index, pr_results.pr_daily.iloc[:, 0], 
                    'b-o', markersize=3, linewidth=1.5, label='Daily PR')
            
            if show_temp_corrected and hasattr(pr_results, 'pr_temp_corrected'):
                ax1.plot(pr_results.pr_temp_corrected.index, 
                        pr_results.pr_temp_corrected.iloc[:, 0], 
                        'r--o', markersize=3, linewidth=1.5, 
                        label='Temperature Corrected PR')
        
        ax1.set_ylabel('Performance Ratio')
        ax1.set_title('Daily Performance Ratio')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Monthly PR
        if hasattr(pr_results, 'pr_monthly') and pr_results.pr_monthly is not None:
            ax2.bar(pr_results.pr_monthly.index, pr_results.pr_monthly.iloc[:, 0], 
                   color='lightblue', alpha=0.7)
        
        ax2.set_ylabel('Performance Ratio')
        ax2.set_xlabel('Date')
        ax2.set_title('Monthly Average Performance Ratio')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_pr_distribution(self, pr_results):
        """Plot PR distribution and statistics"""
        if self.config.interactive:
            return self._plot_pr_distribution_plotly(pr_results)
        else:
            return self._plot_pr_distribution_matplotlib(pr_results)
    
    def _plot_pr_distribution_plotly(self, pr_results):
        """Interactive PR distribution using Plotly"""
        if not hasattr(pr_results, 'pr_daily') or pr_results.pr_daily is None:
            return None
            
        pr_data = pr_results.pr_daily.iloc[:, 0].dropna()
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('PR Distribution', 'PR Box Plot'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Histogram
        fig.add_trace(
            go.Histogram(
                x=pr_data,
                nbinsx=50,
                name='PR Distribution',
                marker_color='lightblue',
                opacity=0.7
            ),
            row=1, col=1
        )
        
        # Box plot
        fig.add_trace(
            go.Box(
                y=pr_data,
                name='PR',
                marker_color='lightgreen'
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            height=400,
            title_text="Performance Ratio Distribution Analysis",
            showlegend=False
        )
        
        return fig
    
    def _plot_pr_distribution_matplotlib(self, pr_results):
        """Static PR distribution using Matplotlib"""
        if not hasattr(pr_results, 'pr_daily') or pr_results.pr_daily is None:
            return None
            
        pr_data = pr_results.pr_daily.iloc[:, 0].dropna()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=self.config.figure_size, 
                                       dpi=self.config.dpi)
        
        # Histogram
        ax1.hist(pr_data, bins=50, alpha=0.7, color='lightblue', edgecolor='black')
        ax1.axvline(pr_data.mean(), color='red', linestyle='--', 
                   label=f'Mean: {pr_data.mean():.3f}')
        ax1.axvline(pr_data.median(), color='green', linestyle='--', 
                   label=f'Median: {pr_data.median():.3f}')
        ax1.set_xlabel('Performance Ratio')
        ax1.set_ylabel('Frequency')
        ax1.set_title('PR Distribution')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Box plot
        ax2.boxplot(pr_data, vert=True)
        ax2.set_ylabel('Performance Ratio')
        ax2.set_title('PR Box Plot')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig


class FaultDetectionPlotter:
    """Visualization tools for fault detection results"""
    
    def __init__(self, config: PlotConfig = None):
        self.config = config or PlotConfig()
    
    def plot_fault_timeline(self, fault_results: Dict[str, Any]):
        """Plot fault detection timeline"""
        if self.config.interactive:
            return self._plot_fault_timeline_plotly(fault_results)
        else:
            return self._plot_fault_timeline_matplotlib(fault_results)
    
    def _plot_fault_timeline_plotly(self, fault_results):
        """Interactive fault timeline using Plotly"""
        fig = go.Figure()
        
        # Plot different types of faults
        fault_types = ['inverter_faults', 'string_faults', 'sensor_faults']
        colors = ['red', 'orange', 'yellow']
        
        for fault_type, color in zip(fault_types, colors):
            if fault_type in fault_results:
                faults = fault_results[fault_type]
                if isinstance(faults, pd.DataFrame) and not faults.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=faults.index,
                            y=[fault_type] * len(faults),
                            mode='markers',
                            name=fault_type.replace('_', ' ').title(),
                            marker=dict(color=color, size=8, symbol='x')
                        )
                    )
        
        fig.update_layout(
            title="Fault Detection Timeline",
            xaxis_title="Date",
            yaxis_title="Fault Type",
            height=400
        )
        
        return fig
    
    def _plot_fault_timeline_matplotlib(self, fault_results):
        """Static fault timeline using Matplotlib"""
        fig, ax = plt.subplots(figsize=self.config.figure_size, dpi=self.config.dpi)
        
        fault_types = ['inverter_faults', 'string_faults', 'sensor_faults']
        colors = ['red', 'orange', 'yellow']
        y_positions = [1, 2, 3]
        
        for fault_type, color, y_pos in zip(fault_types, colors, y_positions):
            if fault_type in fault_results:
                faults = fault_results[fault_type]
                if isinstance(faults, pd.DataFrame) and not faults.empty:
                    ax.scatter(faults.index, [y_pos] * len(faults), 
                             c=color, marker='x', s=50, 
                             label=fault_type.replace('_', ' ').title())
        
        ax.set_yticks(y_positions)
        ax.set_yticklabels([ft.replace('_', ' ').title() for ft in fault_types])
        ax.set_xlabel('Date')
        ax.set_title('Fault Detection Timeline')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_fault_heatmap(self, fault_results: Dict[str, Any]):
        """Plot fault occurrence heatmap"""
        if not fault_results:
            return None
            
        if self.config.interactive:
            return self._plot_fault_heatmap_plotly(fault_results)
        else:
            return self._plot_fault_heatmap_matplotlib(fault_results)
    
    def _plot_fault_heatmap_plotly(self, fault_results):
        """Interactive fault heatmap using Plotly"""
        # This would need actual fault data structure to implement properly
        # For now, return a placeholder
        fig = go.Figure(data=go.Heatmap(
            z=[[1, 0, 1], [0, 1, 0], [1, 1, 0]],
            x=['Inverter 1', 'Inverter 2', 'Inverter 3'],
            y=['Week 1', 'Week 2', 'Week 3'],
            colorscale='Reds'
        ))
        
        fig.update_layout(
            title="Fault Occurrence Heatmap",
            xaxis_title="Equipment",
            yaxis_title="Time Period"
        )
        
        return fig
    
    def _plot_fault_heatmap_matplotlib(self, fault_results):
        """Static fault heatmap using Matplotlib"""
        # Placeholder implementation
        fig, ax = plt.subplots(figsize=self.config.figure_size, dpi=self.config.dpi)
        
        data = np.random.randint(0, 2, (10, 5))  # Placeholder data
        im = ax.imshow(data, cmap='Reds', aspect='auto')
        
        ax.set_xlabel('Equipment ID')
        ax.set_ylabel('Time Period')
        ax.set_title('Fault Occurrence Heatmap')
        
        plt.colorbar(im, ax=ax, label='Fault Occurrence')
        plt.tight_layout()
        return fig


class StatisticalPlotter:
    """Visualization tools for statistical analysis results"""
    
    def __init__(self, config: PlotConfig = None):
        self.config = config or PlotConfig()
    
    def plot_availability_stats(self, availability_stats):
        """Plot data availability statistics"""
        if self.config.interactive:
            return self._plot_availability_plotly(availability_stats)
        else:
            return self._plot_availability_matplotlib(availability_stats)
    
    def _plot_availability_plotly(self, availability_stats):
        """Interactive availability stats using Plotly"""
        if not hasattr(availability_stats, 'daily_availability'):
            return None
            
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Daily Data Availability', 'Monthly Summary'),
            shared_xaxes=True
        )
        
        daily_data = availability_stats.daily_availability
        if daily_data is not None and not daily_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=daily_data.index,
                    y=daily_data.iloc[:, 0] * 100,  # Convert to percentage
                    mode='lines+markers',
                    name='Daily Availability %',
                    line=dict(color='green', width=2)
                ),
                row=1, col=1
            )
        
        # Monthly summary
        if hasattr(availability_stats, 'monthly_availability'):
            monthly_data = availability_stats.monthly_availability
            if monthly_data is not None and not monthly_data.empty:
                fig.add_trace(
                    go.Bar(
                        x=monthly_data.index,
                        y=monthly_data.iloc[:, 0] * 100,
                        name='Monthly Availability %',
                        marker_color='lightgreen'
                    ),
                    row=2, col=1
                )
        
        fig.update_layout(
            height=600,
            title_text="Data Availability Analysis"
        )
        
        fig.update_yaxes(title_text="Availability %", row=1, col=1)
        fig.update_yaxes(title_text="Availability %", row=2, col=1)
        fig.update_xaxes(title_text="Date", row=2, col=1)
        
        return fig
    
    def _plot_availability_matplotlib(self, availability_stats):
        """Static availability stats using Matplotlib"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.config.figure_size, 
                                       dpi=self.config.dpi)
        
        # Daily availability
        if hasattr(availability_stats, 'daily_availability'):
            daily_data = availability_stats.daily_availability
            if daily_data is not None and not daily_data.empty:
                ax1.plot(daily_data.index, daily_data.iloc[:, 0] * 100, 
                        'g-', linewidth=1.5)
                ax1.axhline(95, color='orange', linestyle='--', 
                           label='95% Threshold')
        
        ax1.set_ylabel('Availability %')
        ax1.set_title('Daily Data Availability')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 105)
        
        # Monthly summary
        if hasattr(availability_stats, 'monthly_availability'):
            monthly_data = availability_stats.monthly_availability
            if monthly_data is not None and not monthly_data.empty:
                ax2.bar(monthly_data.index, monthly_data.iloc[:, 0] * 100, 
                       color='lightgreen', alpha=0.7)
        
        ax2.set_ylabel('Availability %')
        ax2.set_xlabel('Date')
        ax2.set_title('Monthly Data Availability')
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 105)
        
        plt.tight_layout()
        return fig
    
    def plot_capacity_analysis(self, capacity_stats):
        """Plot plant capacity analysis"""
        # Implementation would depend on the structure of capacity_stats
        fig, ax = plt.subplots(figsize=self.config.figure_size, dpi=self.config.dpi)
        
        ax.text(0.5, 0.5, 'Capacity Analysis Plot\n(Implementation depends on data structure)', 
                transform=ax.transAxes, ha='center', va='center', fontsize=14)
        ax.set_title('Plant Capacity Analysis')
        
        return fig


class QuickVisualizer:
    """Quick visualization tool for rapid analytics results review"""
    
    def __init__(self, interactive: bool = True):
        self.config = PlotConfig(interactive=interactive)
        self.pr_plotter = PerformancePlotter(self.config)
        self.fault_plotter = FaultDetectionPlotter(self.config)
        self.stats_plotter = StatisticalPlotter(self.config)
    
    def quick_overview(self, analysis_results: Dict[str, Any]):
        """Generate a quick overview of all analysis results"""
        plots = {}
        
        # Performance plots
        if 'pr_results' in analysis_results:
            plots['pr_timeseries'] = self.pr_plotter.plot_pr_timeseries(
                analysis_results['pr_results']
            )
            plots['pr_distribution'] = self.pr_plotter.plot_pr_distribution(
                analysis_results['pr_results']
            )
        
        # Fault detection plots  
        if 'fault_results' in analysis_results:
            plots['fault_timeline'] = self.fault_plotter.plot_fault_timeline(
                analysis_results['fault_results']
            )
            plots['fault_heatmap'] = self.fault_plotter.plot_fault_heatmap(
                analysis_results['fault_results']
            )
        
        # Statistical plots
        if 'availability_stats' in analysis_results:
            plots['availability'] = self.stats_plotter.plot_availability_stats(
                analysis_results['availability_stats']
            )
        
        return plots
    
    def show_all_plots(self, plots: Dict[str, Any]):
        """Display all plots (interactive or save static plots)"""
        if self.config.interactive:
            # For interactive plots, return them for display in notebook/app
            return plots
        else:
            # For static plots, save them
            for plot_name, fig in plots.items():
                if fig is not None:
                    fig.savefig(f'{plot_name}.png', dpi=self.config.dpi, 
                              bbox_inches='tight')
                    plt.close(fig)
            
            print(f"Saved {len([p for p in plots.values() if p is not None])} plots")
            return plots