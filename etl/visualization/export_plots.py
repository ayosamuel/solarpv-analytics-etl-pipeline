"""
Plot export and report generation utilities
"""

import os
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import json


class PlotExporter:
    """Export plots in various formats"""
    
    def __init__(self, output_dir: str = "plots"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export_plots(self, plots: Dict[str, Any], plant_name: str = "plant", 
                    formats: List[str] = None):
        """Export plots in specified formats"""
        if formats is None:
            formats = ['png', 'html']
            
        exported_files = []
        
        for plot_name, plot_obj in plots.items():
            if plot_obj is None:
                continue
                
            for fmt in formats:
                filename = f"{plant_name}_{plot_name}.{fmt}"
                filepath = self.output_dir / filename
                
                try:
                    if fmt == 'png' and hasattr(plot_obj, 'savefig'):
                        # Matplotlib figure
                        plot_obj.savefig(filepath, dpi=300, bbox_inches='tight')
                        exported_files.append(str(filepath))
                    elif fmt == 'html' and hasattr(plot_obj, 'write_html'):
                        # Plotly figure
                        plot_obj.write_html(str(filepath))
                        exported_files.append(str(filepath))
                    elif fmt == 'json' and hasattr(plot_obj, 'to_json'):
                        # Plotly figure to JSON
                        with open(filepath, 'w') as f:
                            f.write(plot_obj.to_json())
                        exported_files.append(str(filepath))
                        
                except Exception as e:
                    print(f"Error exporting {plot_name} as {fmt}: {e}")
        
        return exported_files
    
    def create_plot_index(self, exported_files: List[str], plant_name: str):
        """Create an HTML index of all exported plots"""
        html_files = [f for f in exported_files if f.endswith('.html')]
        
        if not html_files:
            return None
            
        index_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{plant_name} - Analytics Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .plot-container {{ margin: 20px 0; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #34495e; }}
                iframe {{ border: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <h1>{plant_name} Analytics Dashboard</h1>
        """
        
        for html_file in html_files:
            plot_name = Path(html_file).stem.replace(f"{plant_name}_", "").replace("_", " ").title()
            index_content += f"""
            <div class="plot-container">
                <h2>{plot_name}</h2>
                <iframe src="{Path(html_file).name}" width="100%" height="600"></iframe>
            </div>
            """
        
        index_content += """
        </body>
        </html>
        """
        
        index_file = self.output_dir / f"{plant_name}_dashboard.html"
        with open(index_file, 'w') as f:
            f.write(index_content)
            
        return str(index_file)


class ReportGenerator:
    """Generate comprehensive analysis reports with plots"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.plot_exporter = PlotExporter(str(self.output_dir / "plots"))
    
    def generate_plant_report(self, analysis_results: Dict[str, Any], 
                            plant_name: str, plots: Dict[str, Any] = None):
        """Generate comprehensive plant analysis report"""
        
        # Export plots if provided
        exported_plots = []
        if plots:
            exported_plots = self.plot_exporter.export_plots(plots, plant_name)
            dashboard_file = self.plot_exporter.create_plot_index(exported_plots, plant_name)
        
        # Generate text report
        report_content = self._generate_report_content(analysis_results, plant_name)
        
        # Save report
        report_file = self.output_dir / f"{plant_name}_analysis_report.html"
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        # Create summary JSON
        summary_file = self.output_dir / f"{plant_name}_summary.json"
        summary_data = self._extract_summary_data(analysis_results, plant_name)
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)
        
        return {
            'report_file': str(report_file),
            'summary_file': str(summary_file),
            'dashboard_file': dashboard_file if plots else None,
            'exported_plots': exported_plots
        }
    
    def _generate_report_content(self, analysis_results: Dict[str, Any], plant_name: str):
        """Generate HTML report content"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{plant_name} - Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 30px 0; }}
                .metric {{ background-color: #e9ecef; padding: 15px; margin: 10px 0; border-radius: 3px; }}
                .alert {{ padding: 15px; margin: 10px 0; border-radius: 3px; }}
                .alert-success {{ background-color: #d4edda; color: #155724; }}
                .alert-warning {{ background-color: #fff3cd; color: #856404; }}
                .alert-danger {{ background-color: #f8d7da; color: #721c24; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{plant_name} Solar Plant Analysis Report</h1>
                <p>Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """
        
        # Performance Ratio Section
        if 'pr_results' in analysis_results:
            html_content += self._generate_pr_section(analysis_results['pr_results'])
        
        # Fault Detection Section
        if 'fault_results' in analysis_results:
            html_content += self._generate_fault_section(analysis_results['fault_results'])
        
        # Statistical Analysis Section
        if 'availability_stats' in analysis_results:
            html_content += self._generate_stats_section(analysis_results['availability_stats'])
        
        html_content += """
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_pr_section(self, pr_results):
        """Generate PR analysis section"""
        section = """
        <div class="section">
            <h2>Performance Ratio Analysis</h2>
        """
        
        if hasattr(pr_results, 'statistics'):
            stats = pr_results.statistics
            section += f"""
            <div class="metric">
                <h3>Key Performance Metrics</h3>
                <ul>
            """
            for key, value in stats.items():
                section += f"<li><strong>{key}:</strong> {value}</li>"
            
            section += """
                </ul>
            </div>
            """
        
        section += "</div>"
        return section
    
    def _generate_fault_section(self, fault_results):
        """Generate fault detection section"""
        section = """
        <div class="section">
            <h2>Fault Detection Results</h2>
        """
        
        total_faults = 0
        for fault_type, faults in fault_results.items():
            if hasattr(faults, '__len__'):
                fault_count = len(faults)
                total_faults += fault_count
                
                alert_class = "alert-success" if fault_count == 0 else "alert-warning" if fault_count < 5 else "alert-danger"
                
                section += f"""
                <div class="alert {alert_class}">
                    <h3>{fault_type.replace('_', ' ').title()}</h3>
                    <p>Detected {fault_count} faults</p>
                </div>
                """
        
        section += f"""
        <div class="metric">
            <h3>Total Faults Detected: {total_faults}</h3>
        </div>
        </div>
        """
        
        return section
    
    def _generate_stats_section(self, availability_stats):
        """Generate statistical analysis section"""
        section = """
        <div class="section">
            <h2>Statistical Analysis</h2>
        """
        
        if hasattr(availability_stats, 'overall_availability'):
            overall_avail = availability_stats.overall_availability
            section += """
            <div class="metric">
                <h3>Data Availability</h3>
                <table>
                    <tr><th>Data Type</th><th>Availability %</th></tr>
            """
            
            for data_type, availability in overall_avail.items():
                section += f"<tr><td>{data_type}</td><td>{availability:.2%}</td></tr>"
            
            section += """
                </table>
            </div>
            """
        
        section += "</div>"
        return section
    
    def _extract_summary_data(self, analysis_results: Dict[str, Any], plant_name: str):
        """Extract summary data for JSON export"""
        summary = {
            'plant_name': plant_name,
            'analysis_timestamp': str(pd.Timestamp.now()),
            'results_summary': {}
        }
        
        # Add PR summary
        if 'pr_results' in analysis_results:
            pr_results = analysis_results['pr_results']
            if hasattr(pr_results, 'statistics'):
                summary['results_summary']['performance_ratio'] = pr_results.statistics
        
        # Add fault summary
        if 'fault_results' in analysis_results:
            fault_results = analysis_results['fault_results']
            fault_summary = {}
            for fault_type, faults in fault_results.items():
                if hasattr(faults, '__len__'):
                    fault_summary[fault_type] = len(faults)
            summary['results_summary']['faults'] = fault_summary
        
        # Add availability summary
        if 'availability_stats' in analysis_results:
            avail_stats = analysis_results['availability_stats']
            if hasattr(avail_stats, 'overall_availability'):
                summary['results_summary']['data_availability'] = avail_stats.overall_availability
        
        return summary


# Import pandas here to avoid issues with the report generation
try:
    import pandas as pd
except ImportError:
    # Fallback for timestamp if pandas not available
    import datetime
    class pd:
        class Timestamp:
            @staticmethod
            def now():
                return datetime.datetime.now()
            
            def strftime(self, fmt):
                return datetime.datetime.now().strftime(fmt)