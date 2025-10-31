"""
Dashboard components for solar analytics visualization
"""

import pandas as pd
from typing import Dict, List, Optional, Union, Any
from .plotters import QuickVisualizer, PlotConfig


class PlantDashboard:
    """Interactive dashboard for single plant analysis"""
    
    def __init__(self, plant_name: str, interactive: bool = True):
        self.plant_name = plant_name
        self.visualizer = QuickVisualizer(interactive=interactive)
        self.analysis_results = {}
    
    def load_results(self, analysis_results: Dict[str, Any]):
        """Load analysis results into dashboard"""
        self.analysis_results = analysis_results
    
    def generate_dashboard(self):
        """Generate complete plant dashboard"""
        if not self.analysis_results:
            return None
            
        plots = self.visualizer.quick_overview(self.analysis_results)
        
        dashboard_data = {
            'plant_name': self.plant_name,
            'plots': plots,
            'summary_stats': self._generate_summary_stats()
        }
        
        return dashboard_data
    
    def _generate_summary_stats(self):
        """Generate summary statistics for dashboard"""
        stats = {'plant_name': self.plant_name}
        
        # PR statistics
        if 'pr_results' in self.analysis_results:
            pr_results = self.analysis_results['pr_results']
            if hasattr(pr_results, 'pr_daily') and pr_results.pr_daily is not None:
                pr_data = pr_results.pr_daily.iloc[:, 0].dropna()
                stats['pr_mean'] = pr_data.mean()
                stats['pr_std'] = pr_data.std()
                stats['pr_min'] = pr_data.min()
                stats['pr_max'] = pr_data.max()
        
        # Availability statistics
        if 'availability_stats' in self.analysis_results:
            avail_stats = self.analysis_results['availability_stats']
            if hasattr(avail_stats, 'overall_availability'):
                stats['data_availability'] = avail_stats.overall_availability
        
        # Fault count
        if 'fault_results' in self.analysis_results:
            fault_results = self.analysis_results['fault_results']
            total_faults = 0
            for fault_type, faults in fault_results.items():
                if isinstance(faults, pd.DataFrame):
                    total_faults += len(faults)
            stats['total_faults'] = total_faults
        
        return stats


class AnalyticsDashboard:
    """Multi-plant analytics dashboard"""
    
    def __init__(self, interactive: bool = True):
        self.plant_dashboards = {}
        self.interactive = interactive
    
    def add_plant(self, plant_name: str, analysis_results: Dict[str, Any]):
        """Add a plant to the multi-plant dashboard"""
        dashboard = PlantDashboard(plant_name, self.interactive)
        dashboard.load_results(analysis_results)
        self.plant_dashboards[plant_name] = dashboard
    
    def generate_comparative_dashboard(self):
        """Generate comparative dashboard across all plants"""
        if not self.plant_dashboards:
            return None
            
        comparative_data = {
            'plants': list(self.plant_dashboards.keys()),
            'plant_summaries': {},
            'comparative_plots': self._generate_comparative_plots()
        }
        
        # Get summary stats for each plant
        for plant_name, dashboard in self.plant_dashboards.items():
            dashboard_data = dashboard.generate_dashboard()
            if dashboard_data:
                comparative_data['plant_summaries'][plant_name] = dashboard_data['summary_stats']
        
        return comparative_data
    
    def _generate_comparative_plots(self):
        """Generate comparative plots across plants"""
        # This would implement cross-plant comparison plots
        # For now, return a placeholder
        return {
            'pr_comparison': None,
            'availability_comparison': None,
            'fault_comparison': None
        }
    
    def get_plant_dashboard(self, plant_name: str):
        """Get dashboard for specific plant"""
        if plant_name in self.plant_dashboards:
            return self.plant_dashboards[plant_name].generate_dashboard()
        return None