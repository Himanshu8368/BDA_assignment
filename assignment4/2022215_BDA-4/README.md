# Wiki-Vote Kafka Streaming Project

Real-time graph analytics using Apache Kafka for the Wiki-Vote dataset.
for running all the different command see execution_guide.md

## 📋 Project Overview

This project implements a complete streaming data pipeline using Apache Kafka to process and analyze the Wikipedia voting network dataset in real-time. It demonstrates:

- **Real-time data streaming** with Kafka
- **Graph metrics computation** (nodes, edges, degree distribution)
- **Sliding window analytics** for throughput monitoring
- **Fault tolerance** with state management
- **Live visualization** of streaming metrics

## 🎯 Ground Truth Metrics

| Metric | Value |
|--------|-------|
| Nodes | 7,115 |
| Edges | 103,689 |
| Nodes in largest WCC | 7,066 (99.3%) |
| Edges in largest WCC | 103,663 (100%) |
| Average clustering coefficient | 0.1409 |
| Number of triangles | 608,389 |
| Diameter | 7 |

## 🚀 Quick Start

### Prerequisites

- Windows 10/11
- Java 17 or later
- Python 3.8 or later
- Apache Kafka (setup using provided PDF guide)

### Installation

1. **Run the setup script:**
```powershell
.\setup.ps1
```

2. **Or install manually:**
```bash
pip install -r requirements.txt
```

3. **Download dataset:**
```bash
# Download from: https://snap.stanford.edu/data/wiki-Vote.txt.gz
# Extract to get wiki-Vote.txt
```

## 📦 Project Structure

```
wiki-vote-kafka/
├── kafka_producer.py          # Basic producer for streaming edges
├── kafka_consumer.py          # Basic consumer with metrics
├── advanced_consumer.py       # Advanced consumer with windowing
├── visualize_metrics.py       # Visualization script
├── requirements.txt           # Python dependencies
├── setup.ps1                  # Setup script
├── README.md                  # This file
├── wiki-Vote.txt              # Dataset (download separately)
├── plots/                     # Generated visualizations
├── logs/                      # Log files
└── state/                     # State checkpoints
```

## 🔧 Usage

### Step 1: Start Kafka

Open PowerShell and start Kafka server:

```powershell
cd C:\kafka\kafka_2.13-4.1.0
.\bin\windows\kafka-server-start.bat .\config\server.properties
```

### Step 2: Create Topic

In a new PowerShell window:

```powershell
cd C:\kafka\kafka_2.13-4.1.0
.\bin\windows\kafka-topics.bat --create --topic wiki-vote --bootstrap-server localhost:9092
```

### Step 3: Start Consumer

Choose one of the consumer options:

**Basic Consumer:**
```bash
python kafka_consumer.py
```

**Advanced Consumer (with windowing and state management):**
```bash
python advanced_consumer.py
```

### Step 4: Start Producer

In another PowerShell window:

```bash
# Basic streaming (1ms delay)
python kafka_producer.py --file wiki-Vote.txt

# Fast streaming (no delay)
python kafka_producer.py --file wiki-Vote.txt --delay 0

# Simulate out-of-order events
python kafka_producer.py --file wiki-Vote.txt --shuffle
```

### Step 5: Visualize Results

After streaming completes:

```bash
python visualize_metrics.py
```

## 📊 Features

### Part A: Data Streaming Setup ✅

- ✅ Apache Kafka installation (KRaft mode)
- ✅ Topic creation (`wiki-vote`)
- ✅ Dataset preprocessing and streaming simulation
- ✅ Configurable delay for realistic streaming

### Part B: Streaming Computation ✅

#### Basic Consumer Features:
- Real-time node and edge counting
- Progress tracking towards ground truth
- Throughput monitoring
- Degree distribution statistics

#### Advanced Consumer Features:
- **Sliding window metrics** (10-second windows)
- **State management** for fault tolerance
- **Time series data collection**
- **Periodic snapshots** for visualization

### Part C: Streaming Challenges ✅

#### 1. Latency Testing
```bash
# Test different delays
python kafka_producer.py --file wiki-Vote.txt --delay 0.001  # 1ms
python kafka_producer.py --file wiki-Vote.txt --delay 0.01   # 10ms
python kafka_producer.py --file wiki-Vote.txt --delay 0.1    # 100ms
```

#### 2. Ordering Issues
```bash
# Simulate out-of-order events
python kafka_producer.py --file wiki-Vote.txt --shuffle
```

#### 3. Fault Tolerance
```bash
# Start consumer
python advanced_consumer.py

# Press Ctrl+C to stop (state is saved)
# Restart - it will resume from last checkpoint
python advanced_consumer.py
```

#### 4. State Management
- Automatic state checkpointing every 5,000 edges
- Persistent storage in `consumer_state.pkl`
- Seamless recovery on restart

## 📈 Outputs

### Console Output

**Producer:**
```
✓ Producer connected to Kafka at localhost:9092
✓ Publishing to topic: wiki-vote
✓ Loaded 103689 edges from dataset

Progress: 10000/103689 (9.6%) | Rate: 1234.5 edges/sec | Edge: 123 → 456
Progress: 20000/103689 (19.3%) | Rate: 1456.7 edges/sec | Edge: 789 → 012
...
✓ Streaming completed!
Total edges streamed: 103689
Average rate: 1500.00 edges/sec
```

**Consumer:**
```
[12:34:56] Edges: 10000
  Nodes: 3421 | Edges: 9987
  Overall rate: 1234.5 edges/sec
  Window rate: 1456.2 edges/sec (last 10s)
  Progress: Nodes 48.1% | Edges 9.6%
```

### Generated Visualizations

1. **metrics_over_time.png** - Time series of nodes, edges, and processing rate
2. **rate_histogram.png** - Distribution of processing rates
3. **cumulative_progress.png** - Progress towards ground truth

### Data Files

- **metrics_timeseries.json** - Time series data for further analysis
- **consumer_state.pkl** - Checkpoint for fault recovery

## 🎓 Assignment Deliverables

### Code Files ✅
- ✅ `kafka_producer.py` - Producer implementation
- ✅ `kafka_consumer.py` - Basic consumer
- ✅ `advanced_consumer.py` - Advanced consumer with windowing

### Report Components ✅

1. **Real-time Metric Plots** - Generated by `visualize_metrics.py`
2. **Streaming Challenges Discussion:**
   - Latency effects documented
   - Out-of-order handling tested
   - Fault tolerance demonstrated
   - State management implemented

## 🔍 Streaming Issues Explored

### 1. Latency Impact

**Experiment:**
- Vary producer delay: 0ms, 1ms, 10ms, 100ms
- Observe consumer processing lag
- Measure end-to-end latency

**Observations:**
- Lower delays increase throughput but require more resources
- Window-based metrics show rate fluctuations
- Consumer keeps pace with producer at reasonable delays

### 2. Event Ordering

**Experiment:**
- Use `--shuffle` flag to randomize edge order
- Compare results with sequential processing

**Observations:**
- Graph metrics remain consistent (commutative operations)
- Sliding window rates show more variance
- Demonstrates eventual consistency

### 3. Fault Tolerance

**Experiment:**
- Stop consumer mid-stream (Ctrl+C)
- Restart consumer
- Verify offset management

**Results:**
- Consumer resumes from last committed offset
- No data loss
- State restored from checkpoint

### 4. State Management

**Implementation:**
- Periodic state snapshots every 5,000 edges
- Serialized state in pickle format
- Automatic recovery on startup

**Benefits:**
- Crash recovery
- Resumable processing
- Consistent metrics across restarts

## 🛠️ Troubleshooting

### Kafka Connection Issues

```bash
# Check if Kafka is running
netstat -an | findstr 9092

# Verify topic exists
cd C:\kafka\kafka_2.13-4.1.0
.\bin\windows\kafka-topics.bat --list --bootstrap-server localhost:9092
```

### Consumer Not Receiving Messages

```bash
# Reset consumer group offset
cd C:\kafka\kafka_2.13-4.1.0
.\bin\windows\kafka-consumer-groups.bat --bootstrap-server localhost:9092 --group wiki-vote-consumer --reset-offsets --to-earliest --topic wiki-vote --execute
```

### Dataset Download Issues

If automatic download fails:
1. Visit: https://snap.stanford.edu/data/wiki-Vote.html
2. Download `wiki-Vote.txt.gz`
3. Extract to get `wiki-Vote.txt`
4. Place in project directory

## 📝 Command Reference

### Producer Commands

```bash
# Basic streaming
python kafka_producer.py --file wiki-Vote.txt

# Custom delay (seconds)
python kafka_producer.py --file wiki-Vote.txt --delay 0.01

# Shuffle for out-of-order simulation
python kafka_producer.py --file wiki-Vote.txt --shuffle

# Custom Kafka server
python kafka_producer.py --file wiki-Vote.txt --server localhost:9092
```

### Consumer Commands

```bash
# Basic consumer
python kafka_consumer.py

# Report every 5000 edges
python kafka_consumer.py --interval 5000

# Enable degree statistics
python kafka_consumer.py --degrees

# Advanced consumer with custom window
python advanced_consumer.py --window 30
```

### Visualization Commands

```bash
# Generate all plots
python visualize_metrics.py

# Custom input file
python visualize_metrics.py --input my_metrics.json

# Save to specific directory
python visualize_metrics.py --output-dir ./plots
```

## 📚 Additional Resources

- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [SNAP Dataset Collection](https://snap.stanford.edu/data/)
- [Kafka Python Client](https://kafka-python.readthedocs.io/)

## 🤝 Contributing

Feel free to extend this project with:
- Additional graph metrics (clustering coefficient, connected components)
- Real-time visualization dashboard
- Multi-consumer parallel processing
- Integration with Apache Storm or Flink

## 📄 License

This project is for educational purposes as part of a data streaming course assignment.

---

**Created for:** Data Streaming Assignment - Wiki-Vote Graph Analytics
**Date:** November 2024