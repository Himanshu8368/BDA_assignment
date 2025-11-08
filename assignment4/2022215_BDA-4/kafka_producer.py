"""
===============================================================================
FILE 1: kafka_producer.py
===============================================================================
"""

# kafka_producer.py
from kafka import KafkaProducer
import time
import json
from datetime import datetime
import argparse

class WikiVoteProducer:
    def __init__(self, bootstrap_servers='localhost:9092', topic='wiki-vote'):
        """Initialize Kafka producer"""
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: str(k).encode('utf-8') if k else None
        )
        print(f"✓ Producer connected to Kafka at {bootstrap_servers}")
        print(f"✓ Publishing to topic: {topic}")
    
    def load_dataset(self, filepath):
        """Load wiki-Vote dataset from file"""
        edges = []
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('#') or not line:
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        source = int(parts[0])
                        target = int(parts[1])
                        edges.append((source, target))
            print(f"✓ Loaded {len(edges)} edges from dataset")
            return edges
        except FileNotFoundError:
            print(f"✗ Error: File '{filepath}' not found")
            return []
        except Exception as e:
            print(f"✗ Error loading dataset: {e}")
            return []
    
    def stream_edges(self, edges, delay=0.001, shuffle=False):
        """Stream edges to Kafka topic"""
        if shuffle:
            import random
            edges = edges.copy()
            random.shuffle(edges)
            print("✓ Edges shuffled to simulate out-of-order streaming")
        
        total_edges = len(edges)
        start_time = time.time()
        
        print(f"\n{'='*60}")
        print(f"Starting to stream {total_edges} edges...")
        print(f"Delay per edge: {delay} seconds")
        print(f"{'='*60}\n")
        
        try:
            for idx, (source, target) in enumerate(edges, 1):
                message = {
                    'edge_id': idx,
                    'source': source,
                    'target': target,
                    'timestamp': datetime.now().isoformat(),
                    'total_edges': total_edges
                }
                
                self.producer.send(self.topic, key=str(source), value=message)
                
                if idx % 1000 == 0 or idx == total_edges:
                    elapsed = time.time() - start_time
                    rate = idx / elapsed if elapsed > 0 else 0
                    progress = (idx / total_edges) * 100
                    print(f"Progress: {idx}/{total_edges} ({progress:.1f}%) | "
                          f"Rate: {rate:.1f} edges/sec | Edge: {source} → {target}")
                
                time.sleep(delay)
            
            self.producer.flush()
            elapsed = time.time() - start_time
            print(f"\n{'='*60}")
            print(f"✓ Streaming completed!")
            print(f"Total edges streamed: {total_edges}")
            print(f"Total time: {elapsed:.2f} seconds")
            print(f"Average rate: {total_edges/elapsed:.2f} edges/sec")
            print(f"{'='*60}")
            
        except KeyboardInterrupt:
            print("\n✗ Streaming interrupted by user")
        except Exception as e:
            print(f"\n✗ Error during streaming: {e}")
        finally:
            self.close()
    
    def close(self):
        """Close producer connection"""
        self.producer.close()
        print("✓ Producer connection closed")

def main():
    parser = argparse.ArgumentParser(description='Stream wiki-Vote dataset to Kafka')
    parser.add_argument('--file', type=str, default='wiki-Vote.txt',
                        help='Path to wiki-Vote.txt dataset file')
    parser.add_argument('--server', type=str, default='localhost:9092',
                        help='Kafka bootstrap server')
    parser.add_argument('--topic', type=str, default='wiki-vote',
                        help='Kafka topic name')
    parser.add_argument('--delay', type=float, default=0.001,
                        help='Delay between messages in seconds')
    parser.add_argument('--shuffle', action='store_true',
                        help='Shuffle edges to simulate out-of-order events')
    
    args = parser.parse_args()
    
    producer = WikiVoteProducer(bootstrap_servers=args.server, topic=args.topic)
    edges = producer.load_dataset(args.file)
    if edges:
        producer.stream_edges(edges, delay=args.delay, shuffle=args.shuffle)

if __name__ == '__main__':
    main()