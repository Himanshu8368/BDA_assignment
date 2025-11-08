# kafka_consumer.py
from kafka import KafkaConsumer
import json
import time
from collections import defaultdict, deque
import argparse
import random

# ---------------------------
# GraphMetrics - final version (sampling diameter)
# ---------------------------
class GraphMetrics:
    def __init__(self):
        # directed edges as (u,v)
        self.edges = set()
        self.nodes = set()

        # adjacency
        self.graph_directed = defaultdict(set)    # for SCC
        self.graph_undirected = defaultdict(set)  # for WCC, triangles, clustering, diameter

        self.in_degree = defaultdict(int)
        self.out_degree = defaultdict(int)

        self.edges_count = 0
        self.start_time = time.time()

    def add_edge(self, source, target):
        if (source, target) in self.edges:
            return
        # ensure integers
        u = int(source)
        v = int(target)
        self.edges.add((u, v))
        self.nodes.add(u)
        self.nodes.add(v)

        self.out_degree[u] += 1
        self.in_degree[v] += 1

        self.graph_directed[u].add(v)
        self.graph_undirected[u].add(v)
        self.graph_undirected[v].add(u)

        self.edges_count += 1

    def get_metrics(self):
        elapsed = time.time() - self.start_time
        return {
            "nodes": len(self.nodes),
            "edges": self.edges_count,
            "elapsed_time": elapsed,
            "edges_per_second": self.edges_count / elapsed if elapsed > 0 else 0.0
        }

    # -------------------------
    # Largest WCC (undirected connectivity)
    # returns: (node_count, directed_edge_count_inside_comp, comp_set)
    # note: directed_edge_count_inside_comp counts all directed edges (u,v) with u and v in comp_set
    # -------------------------
    def largest_WCC(self):
        visited = set()
        best_comp = []

        for start in self.nodes:
            if start in visited:
                continue
            stack = [start]
            comp = []
            while stack:
                u = stack.pop()
                if u in visited:
                    continue
                visited.add(u)
                comp.append(u)
                for v in self.graph_undirected[u]:
                    if v not in visited:
                        stack.append(v)
            if len(comp) > len(best_comp):
                best_comp = comp

        comp_set = set(best_comp)

        # count directed edges with both endpoints in comp_set (do not dedupe opposite directions)
        directed_edges_inside = 0
        for (u, v) in self.edges:
            if u in comp_set and v in comp_set:
                directed_edges_inside += 1

        return len(comp_set), directed_edges_inside, comp_set

    # -------------------------
    # Largest SCC (Kosaraju)
    # returns: (node_count, directed_edges_inside_scc)
    # -------------------------
    def largest_SCC(self):
        visited = set()
        order = []

        def dfs1(u):
            visited.add(u)
            for v in self.graph_directed[u]:
                if v not in visited:
                    dfs1(v)
            order.append(u)

        for u in self.nodes:
            if u not in visited:
                dfs1(u)

        reverse = defaultdict(set)
        for u in self.graph_directed:
            for v in self.graph_directed[u]:
                reverse[v].add(u)

        visited.clear()
        largest_comp = []

        def dfs2(u, comp):
            stack = [u]
            while stack:
                x = stack.pop()
                if x not in visited:
                    visited.add(x)
                    comp.append(x)
                    for y in reverse[x]:
                        if y not in visited:
                            stack.append(y)

        for u in reversed(order):
            if u not in visited:
                comp = []
                dfs2(u, comp)
                if len(comp) > len(largest_comp):
                    largest_comp = comp

        comp_set = set(largest_comp)
        scc_edges = sum(1 for (u, v) in self.edges if u in comp_set and v in comp_set)
        return len(largest_comp), scc_edges

    # -------------------------
    # Build compact adjacency lists for WCC (dense indices 0..n-1)
    # returns idx_of, node_of, neigh (list of sorted neighbor idx lists), deg
    # -------------------------
    def _build_compact_wcc(self, comp_set):
        node_list = sorted(comp_set)
        idx_of = {node: i for i, node in enumerate(node_list)}
        node_of = {i: node for i, node in enumerate(node_list)}
        n = len(node_list)
        neigh = [[] for _ in range(n)]
        deg = [0] * n

        for u in node_list:
            ui = idx_of[u]
            nbrs = [idx_of[v] for v in self.graph_undirected[u] if v in comp_set]
            neigh[ui] = sorted(set(nbrs))
            deg[ui] = len(neigh[ui])

        return idx_of, node_of, neigh, deg

    # -------------------------
    # Hybrid triangle + per-node triangle counts on WCC
    # Returns: (triangles_unique, avg_clustering, tri_count_per_node_dict)
    # -------------------------
    def triangles_and_clustering_on_wcc(self, comp_set):
        if not comp_set:
            return 0, 0.0, {}

        idx_of, node_of, neigh, deg = self._build_compact_wcc(comp_set)
        n = len(neigh)

        # forward adjacency by degree-ordering
        forward = [[] for _ in range(n)]
        for u in range(n):
            du = deg[u]
            for v in neigh[u]:
                if du < deg[v] or (du == deg[v] and u < v):
                    forward[u].append(v)

        forward_sets = [set(lst) for lst in forward]

        triangles = 0
        tri_count_per_node = [0] * n

        for u in range(n):
            for v in forward[u]:
                # choose smaller forward list to iterate
                if len(forward[u]) < len(forward[v]):
                    small = forward[u]
                    big_set = forward_sets[v]
                else:
                    small = forward[v]
                    big_set = forward_sets[u]
                for w in small:
                    if w in big_set:
                        triangles += 1
                        tri_count_per_node[u] += 1
                        tri_count_per_node[v] += 1
                        tri_count_per_node[w] += 1

        # compute per-node local clustering and average over nodes in WCC
        clustering_sum = 0.0
        for u in range(n):
            d = deg[u]
            if d < 2:
                cu = 0.0
            else:
                cu = (2.0 * tri_count_per_node[u]) / (d * (d - 1))
            clustering_sum += cu

        avg_clustering = clustering_sum / n if n > 0 else 0.0

        # map tri counts back to original node ids
        tri_count_per_node_dict = { node_of[i]: tri_count_per_node[i] for i in range(n) }

        return int(triangles), float(avg_clustering), tri_count_per_node_dict

    # -------------------------
    # BFS on compact adjacency lists (indices)
    # returns dict idx -> distance for reachable nodes
    # -------------------------
    def _bfs_compact(self, start_idx, neigh, allowed_idx_set):
        dist = [-1] * len(neigh)
        dq = deque()
        dist[start_idx] = 0
        dq.append(start_idx)
        while dq:
            u = dq.popleft()
            for v in neigh[u]:
                if v in allowed_idx_set and dist[v] == -1:
                    dist[v] = dist[u] + 1
                    dq.append(v)
        return {i: d for i, d in enumerate(dist) if d != -1}

    # -------------------------
    # Sampling-based diameter & effective diameter on WCC (Option 2)
    # -------------------------
    def diameter_and_effective_on_wcc(self, comp_set, sample_count=100):
        if not comp_set:
            return 0, 0.0

        idx_of, node_of, neigh, deg = self._build_compact_wcc(comp_set)
        n = len(neigh)
        allowed_idx = set(range(n))

        samples = min(sample_count, n)
        picks = random.sample(range(n), samples) if samples > 0 else []

        ecc_list = []
        all_dists = []
        for s in picks:
            distmap = self._bfs_compact(s, neigh, allowed_idx)
            if not distmap:
                continue
            ecc = max(distmap.values())
            ecc_list.append(ecc)
            all_dists.extend(distmap.values())

        diameter = int(max(ecc_list)) if ecc_list else 0
        effective = 0.0
        if all_dists:
            all_dists.sort()
            idx90 = int(0.9 * len(all_dists))
            effective = float(all_dists[idx90])

        return diameter, effective


# ---------------------------
# Consumer + reporting
# ---------------------------
class WikiVoteConsumer:
    GROUND_TRUTH = {
        "nodes": 7115,
        "edges": 103689,
        "wcc_nodes": 7066,
        "wcc_edges": 103585,
        "wcc_fraction": 0.9931,
        "scc_nodes": 1300,
        "scc_edges": 39456,
        "scc_fraction": 0.1827,
        "triangles": 608389,
        "closed_fraction": 0.04183,
        "clustering": 0.14091,
        "diameter": 7,
        "effective": 3.8
    }

    def __init__(self, bootstrap_servers='localhost:9092', topic='wiki-vote', group_id='wiki-consumer'):
        self.topic = topic
        self.metrics = GraphMetrics()
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest'
        )
        print(f"✓ Consumer connected to {bootstrap_servers}")
        print(f"✓ Subscribed to topic: {topic}\n")

    def process_stream(self, report_interval=1000, enable_analytics=False):
        self.enable_analytics = enable_analytics
        print("Streaming started...\n")
        count = 0
        try:
            for msg in self.consumer:
                data = msg.value
                self.metrics.add_edge(int(data["source"]), int(data["target"]))
                count += 1
                if count % report_interval == 0:
                    self._report(count)
                m = self.metrics.get_metrics()
                if m["nodes"] >= self.GROUND_TRUTH["nodes"] and m["edges"] >= self.GROUND_TRUTH["edges"]:
                    self._report(count)
                    break
        finally:
            self._final_report()
            self.consumer.close()

    def _report(self, count):
        m = self.metrics.get_metrics()
        print(f"Processed edges: {count:,}")
        print(f"  Nodes: {m['nodes']:,}")
        print(f"  Edges: {m['edges']:,}\n")

    def _final_report(self):
        print("\n" + "=" * 80)
        print("FINAL STATISTICS")
        print("=" * 80)

        m = self.metrics.get_metrics()
        print(f"Nodes: {m['nodes']:,}")
        print(f"Edges: {m['edges']:,}")
        print(f"Rate: {m['edges_per_second']:.1f} edges/sec\n")

        if not self.enable_analytics:
            return

        # Largest WCC (undirected connectivity), wcc_edges counted as directed edges inside component
        wcc_nodes, wcc_edges, wcc_set = self.metrics.largest_WCC()

        # Largest SCC (directed)
        scc_nodes, scc_edges = self.metrics.largest_SCC()

        # Triangles and avg clustering on WCC
        triangles, avg_clustering, tri_count_per_node = self.metrics.triangles_and_clustering_on_wcc(wcc_set)

        # Triples inside WCC: sum C(deg(u),2) over nodes in WCC
        triples = 0.0
        for u in wcc_set:
            d = len([v for v in self.metrics.graph_undirected[u] if v in wcc_set])
            if d >= 2:
                triples += d * (d - 1) / 2.0

        # Closed triangle fraction (closed triplets / total triplets) = (3 * triangles) / triples
        closed_fraction = (3.0 * triangles / triples) if triples > 0 else 0.0

        # Diameter & effective diameter (sampling)
        diameter, effective = self.metrics.diameter_and_effective_on_wcc(wcc_set, sample_count=100)

        comp = {
            "nodes": m["nodes"],
            "edges": m["edges"],
            "wcc_nodes": wcc_nodes,
            "wcc_edges": wcc_edges,
            "wcc_fraction": wcc_nodes / m["nodes"] if m["nodes"] else 0.0,
            "scc_nodes": scc_nodes,
            "scc_edges": scc_edges,
            "scc_fraction": scc_nodes / m["nodes"] if m["nodes"] else 0.0,
            "triangles": triangles,
            "clustering": avg_clustering,
            "closed_fraction": closed_fraction,
            "diameter": diameter,
            "effective": effective
        }

        GT = self.GROUND_TRUTH

        print("=" * 80)
        print(f"{'Metric':35} {'Ground Truth':>15} {'Computed':>15} {'Diff':>15}")
        print("-" * 80)

        def fmt_val_print(x):
            if isinstance(x, int) or (isinstance(x, float) and x.is_integer()):
                return f"{int(round(x))}"
            return f"{x:.5f}"

        def row(name, key):
            gt = GT[key]
            c = comp[key]
            diff = c - gt
            print(f"{name:35} {fmt_val_print(gt):>15} {fmt_val_print(c):>15} {fmt_val_print(diff):>15}")

        row("Nodes", "nodes")
        row("Edges", "edges")
        row("Largest WCC (nodes)", "wcc_nodes")
        row("WCC fraction", "wcc_fraction")
        row("Largest WCC (edges)", "wcc_edges")
        row("Largest SCC (nodes)", "scc_nodes")
        row("SCC fraction", "scc_fraction")
        row("Largest SCC (edges)", "scc_edges")
        row("Avg clustering coefficient", "clustering")
        row("Triangles", "triangles")
        row("Closed triangles fraction", "closed_fraction")
        row("Diameter", "diameter")
        row("Effective diameter", "effective")

        print("=" * 80 + "\n")


# ---------------------------
# CLI
# ---------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="localhost:9092")
    parser.add_argument("--topic", default="wiki-vote")
    parser.add_argument("--group", default="wiki-consumer")
    parser.add_argument("--interval", type=int, default=1000)
    parser.add_argument("--analytics", action="store_true")
    args = parser.parse_args()

    consumer = WikiVoteConsumer(args.server, args.topic, args.group)
    consumer.process_stream(report_interval=args.interval, enable_analytics=args.analytics)


if __name__ == "__main__":
    main()
