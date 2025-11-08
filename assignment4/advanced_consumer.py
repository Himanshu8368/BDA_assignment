# Save this as create_files.ps1 and run it in PowerShell
# This will create both advanced_consumer.py and visualize_metrics.py

from kafka import KafkaConsumer
import json
import time
import pickle
import argparse
from datetime import datetime
from pathlib import Path
from collections import deque

class AdvancedGraphMetrics:
    def __init__(self, window_size=10):
        self.edges = set()
        self.nodes = set()
        self.edges_count = 0
        self.start_time = time.time()
        self.window_size = window_size
        self.window_events = deque()
        self.metrics_history = []
        
    def add_edge(self, source, target):
        u, v = int(source), int(target)
        if (u, v) in self.edges:
            return
        self.edges.add((u, v))
        self.nodes.add(u)
        self.nodes.add(v)
        self.edges_count += 1
        current_time = time.time()
        self.window_events.append((current_time, 1))
        cutoff_time = current_time - self.window_size
        while self.window_events and self.window_events[0][0] < cutoff_time:
            self.window_events.popleft()
    
    def get_window_rate(self):
        if not self.window_events:
            return 0.0
        window_duration = time.time() - self.window_events[0][0]
        if window_duration == 0:
            return 0.0
        window_edges = sum(count for _, count in self.window_events)
        return window_edges / window_duration
    
    def get_metrics(self):
        elapsed = time.time() - self.start_time
        overall_rate = self.edges_count / elapsed if elapsed > 0 else 0.0
        window_rate = self.get_window_rate()
        return {
            "timestamp": datetime.now().isoformat(),
            "elapsed_time": elapsed,
            "nodes": len(self.nodes),
            "edges": self.edges_count,
            "edges_per_second": overall_rate,
            "window_rate": window_rate
        }
    
    def save_metrics_snapshot(self):
        self.metrics_history.append(self.get_metrics())

class AdvancedWikiVoteConsumer:
    GROUND_TRUTH = {
        "nodes": 7115,
        "edges": 103689,
        "wcc_nodes": 7066,
        "wcc_edges": 103585,
        "scc_nodes": 1300,
        "triangles": 608389
    }
    
    def __init__(self, bootstrap_servers='localhost:9092', 
                 topic='wiki-vote', group_id='wiki-consumer-advanced',
                 window_size=10):
        self.topic = topic
        self.group_id = group_id
        self.window_size = window_size
        self.metrics = AdvancedGraphMetrics(window_size=window_size)
        self.state_dir = Path('state')
        self.state_dir.mkdir(exist_ok=True)
        self.state_file = self.state_dir / f'{group_id}_state.pkl'
        self.metrics_file = 'metrics_timeseries.json'
        
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            auto_commit_interval_ms=5000
        )
        
        print(f"✓ Advanced consumer connected")
        print(f"  Bootstrap servers: {bootstrap_servers}")
        print(f"  Topic: {topic}")
        print(f"  Consumer group: {group_id}")
        print(f"  Sliding window size: {window_size}s\n")
        self.load_state()
    
    def save_state(self):
        state = {
            'edges': self.metrics.edges,
            'nodes': self.metrics.nodes,
            'edges_count': self.metrics.edges_count,
            'start_time': self.metrics.start_time,
            'metrics_history': self.metrics.metrics_history,
            'timestamp': datetime.now().isoformat()
        }
        try:
            with open(self.state_file, 'wb') as f:
                pickle.dump(state, f)
            print(f"  💾 State saved ({len(self.metrics.nodes)} nodes, {self.metrics.edges_count} edges)")
        except Exception as e:
            print(f"  ✗ Failed to save state: {e}")
    
    def load_state(self):
        if not self.state_file.exists():
            return
        try:
            with open(self.state_file, 'rb') as f:
                state = pickle.load(f)
            self.metrics.edges = state['edges']
            self.metrics.nodes = state['nodes']
            self.metrics.edges_count = state['edges_count']
            self.metrics.start_time = state['start_time']
            self.metrics.metrics_history = state.get('metrics_history', [])
            print(f"✓ Loaded previous state from {state['timestamp']}")
            print(f"  Previous progress: {self.metrics.edges_count:,} edges, {len(self.metrics.nodes):,} nodes")
            print(f"✓ State restored successfully\n")
        except Exception as e:
            print(f"✗ Failed to load state: {e}\n")
    
    def save_metrics_to_file(self):
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics.metrics_history, f, indent=2)
            print(f"  📊 Metrics saved to {self.metrics_file}")
        except Exception as e:
            print(f"  ✗ Failed to save metrics: {e}")
    
    def process_stream(self, report_interval=1000, state_save_interval=5000, plot_save_interval=10000):
        print("Starting advanced real-time processing...")
        print(f"Report interval: every {report_interval} edges")
        print(f"State save interval: every {state_save_interval} edges")
        print(f"Plot save interval: every {plot_save_interval} edges\n")
        
        count = 0
        last_report = 0
        
        try:
            for msg in self.consumer:
                data = msg.value
                self.metrics.add_edge(int(data["source"]), int(data["target"]))
                count += 1
                
                if count - last_report >= report_interval:
                    self._report(count)
                    last_report = count
                
                if count % state_save_interval == 0:
                    self.metrics.save_metrics_snapshot()
                    self.save_state()
                
                if count % plot_save_interval == 0:
                    self.metrics.save_metrics_snapshot()
                    self.save_metrics_to_file()
                
                m = self.metrics.get_metrics()
                if (m["nodes"] >= self.GROUND_TRUTH["nodes"] and m["edges"] >= self.GROUND_TRUTH["edges"]):
                    self._report(count)
                    break
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Consumer interrupted by user")
            print("Saving current state before exit...\n")
        
        finally:
            self._final_report()
            self.metrics.save_metrics_snapshot()
            self.save_state()
            self.save_metrics_to_file()
            self.consumer.close()
            print("\n✓ Consumer closed gracefully")
    
    def _report(self, count):
        m = self.metrics.get_metrics()
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] Edges: {count:,}")
        print(f"  Nodes: {m['nodes']:,} | Edges: {m['edges']:,}")
        print(f"  Overall rate: {m['edges_per_second']:.1f} edges/sec")
        print(f"  Window rate: {m['window_rate']:.1f} edges/sec (last {self.window_size}s)")
        node_pct = (m['nodes'] / self.GROUND_TRUTH['nodes']) * 100
        edge_pct = (m['edges'] / self.GROUND_TRUTH['edges']) * 100
        print(f"  Progress: Nodes {node_pct:.1f}% | Edges {edge_pct:.1f}%\n")
    
    def _final_report(self):
        print("\n" + "=" * 80)
        print("FINAL ADVANCED CONSUMER STATISTICS")
        print("=" * 80)
        m = self.metrics.get_metrics()
        print(f"\nFinal Counts:")
        print(f"  Nodes: {m['nodes']:,}")
        print(f"  Edges: {m['edges']:,}")
        print(f"  Processing time: {m['elapsed_time']:.2f} seconds ({m['elapsed_time']/60:.2f} minutes)")
        print(f"  Average rate: {m['edges_per_second']:.1f} edges/sec")
        print(f"\nComparison with Ground Truth:")
        print(f"  {'Metric':<20} {'Ground Truth':>15} {'Computed':>15} {'Match':>10}")
        print(f"  {'-'*20} {'-'*15} {'-'*15} {'-'*10}")
        
        def check_match(computed, truth, tolerance=0):
            return "✓" if abs(computed - truth) <= tolerance else "✗"
        
        print(f"  {'Nodes':<20} {self.GROUND_TRUTH['nodes']:>15,} {m['nodes']:>15,} {check_match(m['nodes'], self.GROUND_TRUTH['nodes']):>10}")
        print(f"  {'Edges':<20} {self.GROUND_TRUTH['edges']:>15,} {m['edges']:>15,} {check_match(m['edges'], self.GROUND_TRUTH['edges']):>10}")
        print(f"\nMetrics History:")
        print(f"  Data points collected: {len(self.metrics.metrics_history)}")
        print(f"  Metrics saved to: {self.metrics_file}")
        print("\n" + "=" * 80 + "\n")

def main():
    parser = argparse.ArgumentParser(description='Advanced Kafka consumer for Wiki-Vote streaming analytics')
    parser.add_argument('--server', default='localhost:9092', help='Kafka bootstrap server')
    parser.add_argument('--topic', default='wiki-vote', help='Kafka topic name')
    parser.add_argument('--group', default='wiki-consumer-advanced', help='Consumer group ID')
    parser.add_argument('--window', type=int, default=10, help='Sliding window size in seconds')
    parser.add_argument('--interval', type=int, default=1000, help='Report interval in edges')
    parser.add_argument('--state-interval', type=int, default=5000, help='State save interval')
    parser.add_argument('--plot-interval', type=int, default=10000, help='Plot data save interval')
    args = parser.parse_args()
    
    consumer = AdvancedWikiVoteConsumer(
        bootstrap_servers=args.server,
        topic=args.topic,
        group_id=args.group,
        window_size=args.window
    )
    
    consumer.process_stream(
        report_interval=args.interval,
        state_save_interval=args.state_interval,
        plot_save_interval=args.plot_interval
    )

if __name__ == "__main__":
    main()
