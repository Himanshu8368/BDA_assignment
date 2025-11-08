import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime

class MetricsVisualizer:
    def __init__(self, metrics_file='metrics_timeseries.json'):
        self.metrics_file = metrics_file
        self.data = None
        self.plots_dir = Path('plots')
        self.plots_dir.mkdir(exist_ok=True)
        
    def load_data(self):
        """Load metrics from JSON file"""
        try:
            with open(self.metrics_file, 'r') as f:
                self.data = json.load(f)
            print(f"✓ Loaded {len(self.data)} data points from {self.metrics_file}\n")
            return True
        except FileNotFoundError:
            print(f"✗ Error: {self.metrics_file} not found!")
            print("  Run advanced_consumer.py first to generate metrics data.")
            return False
        except json.JSONDecodeError:
            print(f"✗ Error: {self.metrics_file} is corrupted!")
            return False
    
    def generate_summary_report(self):
        """Print summary statistics"""
        if not self.data:
            return
        
        print("=" * 80)
        print("STREAMING METRICS SUMMARY REPORT")
        print("=" * 80 + "\n")
        
        # Extract data
        timestamps = [d['elapsed_time'] for d in self.data]
        nodes = [d['nodes'] for d in self.data]
        edges = [d['edges'] for d in self.data]
        rates = [d['edges_per_second'] for d in self.data]
        window_rates = [d.get('window_rate', 0) for d in self.data]
        
        # Duration
        duration = timestamps[-1] - timestamps[0]
        print(f"Processing Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        print(f"Final Node Count: {nodes[-1]:,}")
        print(f"Final Edge Count: {edges[-1]:,}\n")
        
        # Rate statistics
        print("Processing Rate Statistics:")
        print(f"  Average: {np.mean(rates):.2f} edges/sec")
        print(f"  Median: {np.median(rates):.2f} edges/sec")
        print(f"  Min: {np.min(rates):.2f} edges/sec")
        print(f"  Max: {np.max(rates):.2f} edges/sec")
        print(f"  Std Dev: {np.std(rates):.2f} edges/sec\n")
        
        if any(window_rates):
            print("Window Rate Statistics:")
            window_rates_clean = [r for r in window_rates if r > 0]
            if window_rates_clean:
                print(f"  Average: {np.mean(window_rates_clean):.2f} edges/sec")
                print(f"  Median: {np.median(window_rates_clean):.2f} edges/sec")
                print(f"  Min: {np.min(window_rates_clean):.2f} edges/sec")
                print(f"  Max: {np.max(window_rates_clean):.2f} edges/sec\n")
    
    def plot_metrics_over_time(self):
        """Create comprehensive time series plots"""
        if not self.data:
            return
        
        # Extract data
        timestamps = [d['elapsed_time'] for d in self.data]
        nodes = [d['nodes'] for d in self.data]
        edges = [d['edges'] for d in self.data]
        rates = [d['edges_per_second'] for d in self.data]
        window_rates = [d.get('window_rate', 0) for d in self.data]
        
        # Create figure with subplots
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        fig.suptitle('Real-Time Streaming Metrics Over Time', fontsize=16, fontweight='bold')
        
        # Plot 1: Nodes and Edges
        ax1 = axes[0]
        ax1_twin = ax1.twinx()
        
        line1 = ax1.plot(timestamps, nodes, 'b-', linewidth=2, label='Nodes', alpha=0.8)
        line2 = ax1_twin.plot(timestamps, edges, 'r-', linewidth=2, label='Edges', alpha=0.8)
        
        ax1.set_xlabel('Time (seconds)', fontsize=10)
        ax1.set_ylabel('Number of Nodes', color='b', fontsize=10)
        ax1_twin.set_ylabel('Number of Edges', color='r', fontsize=10)
        ax1.tick_params(axis='y', labelcolor='b')
        ax1_twin.tick_params(axis='y', labelcolor='r')
        ax1.grid(True, alpha=0.3)
        ax1.set_title('Graph Size Growth', fontsize=12, fontweight='bold')
        
        # Combined legend
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left')
        
        # Plot 2: Processing Rate
        ax2 = axes[1]
        ax2.plot(timestamps, rates, 'g-', linewidth=2, label='Overall Rate', alpha=0.8)
        if any(window_rates):
            ax2.plot(timestamps, window_rates, 'orange', linewidth=2, 
                    label='Window Rate', alpha=0.6, linestyle='--')
        
        ax2.set_xlabel('Time (seconds)', fontsize=10)
        ax2.set_ylabel('Edges per Second', fontsize=10)
        ax2.set_title('Processing Throughput', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='best')
        
        # Add average line
        avg_rate = np.mean(rates)
        ax2.axhline(y=avg_rate, color='r', linestyle=':', linewidth=2, 
                   label=f'Average: {avg_rate:.1f} edges/sec', alpha=0.7)
        ax2.legend(loc='best')
        
        # Plot 3: Progress to Ground Truth
        ax3 = axes[2]
        node_progress = [(n / 7115) * 100 for n in nodes]
        edge_progress = [(e / 103689) * 100 for e in edges]
        
        ax3.plot(timestamps, node_progress, 'b-', linewidth=2, 
                label='Nodes Progress', alpha=0.8)
        ax3.plot(timestamps, edge_progress, 'r-', linewidth=2, 
                label='Edges Progress', alpha=0.8)
        ax3.axhline(y=100, color='green', linestyle='--', linewidth=2, 
                   label='100% Target', alpha=0.7)
        
        ax3.set_xlabel('Time (seconds)', fontsize=10)
        ax3.set_ylabel('Progress (%)', fontsize=10)
        ax3.set_title('Convergence to Ground Truth', fontsize=12, fontweight='bold')
        ax3.set_ylim([0, 105])
        ax3.grid(True, alpha=0.3)
        ax3.legend(loc='best')
        
        plt.tight_layout()
        
        # Save plot
        output_file = self.plots_dir / 'metrics_over_time.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Saved plot to {output_file}")
        plt.close()
    
    def plot_rate_histogram(self):
        """Create histogram of processing rates"""
        if not self.data:
            return
        
        rates = [d['edges_per_second'] for d in self.data if d['edges_per_second'] > 0]
        
        if not rates:
            print("✗ No rate data available for histogram")
            return
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create histogram
        n, bins, patches = ax.hist(rates, bins=30, color='steelblue', 
                                    edgecolor='black', alpha=0.7)
        
        # Add statistics lines
        mean_rate = np.mean(rates)
        median_rate = np.median(rates)
        
        ax.axvline(mean_rate, color='red', linestyle='--', linewidth=2, 
                  label=f'Mean: {mean_rate:.1f}')
        ax.axvline(median_rate, color='green', linestyle='--', linewidth=2, 
                  label=f'Median: {median_rate:.1f}')
        
        ax.set_xlabel('Edges per Second', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title('Distribution of Processing Rates', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        # Save plot
        output_file = self.plots_dir / 'rate_histogram.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Saved histogram to {output_file}")
        plt.close()
    
    def plot_cumulative_progress(self):
        """Create cumulative progress plot"""
        if not self.data:
            return
        
        edges = [d['edges'] for d in self.data]
        timestamps = [d['elapsed_time'] for d in self.data]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.plot(timestamps, edges, 'b-', linewidth=2, alpha=0.8)
        ax.axhline(y=103689, color='red', linestyle='--', linewidth=2, 
                  label='Target: 103,689 edges', alpha=0.7)
        
        # Fill area under curve
        ax.fill_between(timestamps, edges, alpha=0.3, color='blue')
        
        ax.set_xlabel('Time (seconds)', fontsize=12)
        ax.set_ylabel('Cumulative Edges Processed', fontsize=12)
        ax.set_title('Cumulative Edge Processing Progress', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Format y-axis with thousands separator
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
        
        plt.tight_layout()
        
        # Save plot
        output_file = self.plots_dir / 'cumulative_progress.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Saved progress plot to {output_file}")
        plt.close()
    
    def generate_all_visualizations(self):
        """Generate all plots and reports"""
        if not self.load_data():
            return False
        
        self.generate_summary_report()
        
        print("=" * 80)
        print("GENERATING VISUALIZATIONS")
        print("=" * 80 + "\n")
        
        self.plot_metrics_over_time()
        self.plot_rate_histogram()
        self.plot_cumulative_progress()
        
        print(f"\n✓ All visualizations generated successfully!")
        print(f"✓ Check the '{self.plots_dir}' directory for output files.\n")
        
        return True


def main():
    visualizer = MetricsVisualizer()
    visualizer.generate_all_visualizations()


if __name__ == "__main__":
    main()