from collections import defaultdict, deque
import time
from typing import Any, Dict, List, Set, Tuple


class GraphNetworkAnalyzer:
    """
    Layer 3: Graph Neural Network & Mule Ring Link Analysis Engine
    Builds a real-time directed payment graph across accounts, cards, and beneficiaries
    to detect Multi-Hop Mule Rings, Smurfing (Fan-Out), and Cyclic Money Laundering.
    """
    def __init__(self):
        # Adjacency list: sender_node -> list of (receiver_node, amount, timestamp, tx_id)
        self.adj = defaultdict(list)
        # Reverse adjacency: receiver_node -> list of (sender_node, amount, timestamp, tx_id)
        self.rev_adj = defaultdict(list)
        # Known flagged mule clusters: set of node_ids
        self.flagged_mule_nodes = set()
        # Seed initial realistic topology so demo graph is rich with nodes & connections
        self._seed_initial_banking_graph()

    def _seed_initial_banking_graph(self):
        now = time.time()
        # Normal merchant hub
        self.add_transaction("ACC_ALICE_101", "MERCHANT_AMAZON", 2500, now - 500, "TX_INIT_1")
        self.add_transaction("ACC_BOB_102", "MERCHANT_AMAZON", 4200, now - 400, "TX_INIT_2")
        self.add_transaction("ACC_CAROL_103", "MERCHANT_FLIPKART", 1800, now - 350, "TX_INIT_3")
        # Known mule ring demo structure (A -> B -> C -> D -> A)
        self.add_transaction("MULE_RING_A", "MULE_RING_B", 45000, now - 250, "TX_MULE_1")
        self.add_transaction("MULE_RING_B", "MULE_RING_C", 44200, now - 200, "TX_MULE_2")
        self.add_transaction("MULE_RING_C", "MULE_RING_D", 43800, now - 150, "TX_MULE_3")
        self.add_transaction("MULE_RING_D", "MULE_RING_A", 43000, now - 100, "TX_MULE_4")
        self.flagged_mule_nodes.update(["MULE_RING_A", "MULE_RING_B", "MULE_RING_C", "MULE_RING_D"])

    def add_transaction(self, sender: str, receiver: str, amount: float, timestamp: float = None, tx_id: str = None):
        if not sender or not receiver:
            return
        ts = timestamp or time.time()
        tx_identifier = tx_id or f"TX_{int(ts * 1000)}"
        self.adj[sender].append((receiver, float(amount), ts, tx_identifier))
        self.rev_adj[receiver].append((sender, float(amount), ts, tx_identifier))

    def detect_cyclic_flow(self, start_node: str, max_depth: int = 5) -> Tuple[bool, List[str]]:
        """
        Detects directed cycles in money flows (e.g. A -> B -> C -> A) indicating money laundering.
        """
        visited = set()
        queue = deque([(start_node, [start_node])])

        while queue:
            current, path = queue.popleft()
            if len(path) > max_depth + 1:
                continue

            for neighbor, amt, ts, txid in self.adj.get(current, []):
                if neighbor == start_node and len(path) >= 3:
                    # Found closed cycle of 3+ hops!
                    return True, path + [start_node]
                if neighbor not in visited and len(path) <= max_depth:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return False, []

    def analyze_smurfing_fan_out(self, sender: str, window_seconds: int = 600) -> Dict[str, Any]:
        """
        Detects Fan-Out Smurfing: 1 sender dispersing funds to 4+ distinct recipients in a short window.
        """
        now = time.time()
        cutoff = now - window_seconds
        recent_transfers = [t for t in self.adj.get(sender, []) if t[2] >= cutoff]
        unique_recipients = set(t[0] for t in recent_transfers)

        is_smurfing = len(unique_recipients) >= 4
        return {
            "is_smurfing": is_smurfing,
            "unique_recipients_count": len(unique_recipients),
            "recent_transfers_count": len(recent_transfers),
            "recipients": list(unique_recipients)[:8],
        }

    def analyze_mule_aggregation_fan_in(self, receiver: str, window_seconds: int = 600) -> Dict[str, Any]:
        """
        Detects Fan-In Mule Aggregation: 1 recipient collecting funds from 3+ distinct senders rapidly.
        """
        now = time.time()
        cutoff = now - window_seconds
        recent_inflows = [t for t in self.rev_adj.get(receiver, []) if t[2] >= cutoff]
        unique_senders = set(t[0] for t in recent_inflows)

        is_mule_aggregator = len(unique_senders) >= 3
        return {
            "is_mule_aggregator": is_mule_aggregator,
            "unique_senders_count": len(unique_senders),
            "senders": list(unique_senders)[:8],
        }

    def evaluate_network_risk(self, sender: str, receiver: str, amount: float) -> Dict[str, Any]:
        """
        Evaluates full Layer 3 Graph Topology risk for a candidate transaction.
        """
        # Record into graph
        self.add_transaction(sender, receiver, amount)

        risk_score = 8.0
        signals = []
        is_mule_syndicate = False
        is_cyclic = False
        cycle_path = []

        # 1. Check for Cyclic Laundering Loops
        cyclic_found, path = self.detect_cyclic_flow(sender, max_depth=4)
        if cyclic_found:
            risk_score += 65.0
            is_cyclic = True
            is_mule_syndicate = True
            cycle_path = path
            signals.append(f"[!] Closed-loop cyclic fund routing detected ({' → '.join(path)}) (Money Laundering)")
            self.flagged_mule_nodes.update(path)

        # 2. Check for Smurfing Fan-Out
        smurf_info = self.analyze_smurfing_fan_out(sender)
        if smurf_info["is_smurfing"]:
            risk_score += 50.0
            is_mule_syndicate = True
            signals.append(f"[!] Rapid Fan-Out Smurfing detected ({smurf_info['unique_recipients_count']} recipients in 10 mins)")
            self.flagged_mule_nodes.add(sender)

        # 3. Check for Mule Aggregation Fan-In on Receiver
        agg_info = self.analyze_mule_aggregation_fan_in(receiver)
        if agg_info["is_mule_aggregator"]:
            risk_score += 45.0
            is_mule_syndicate = True
            signals.append(f"[!] Destination account exhibits Fan-In Mule Funneling ({agg_info['unique_senders_count']} upstream senders)")
            self.flagged_mule_nodes.add(receiver)

        # 4. Proximity to Known Flagged Mule Nodes
        if sender in self.flagged_mule_nodes or receiver in self.flagged_mule_nodes:
            risk_score += 40.0
            is_mule_syndicate = True
            signals.append("[!] Direct interaction with flagged high-risk mule syndicate account")

        # Normalization
        risk_score = max(5.0, min(100.0, risk_score))

        if risk_score >= 70.0:
            risk_level = "CRITICAL"
        elif risk_score >= 45.0:
            risk_level = "HIGH"
        elif risk_score >= 25.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
            if not signals:
                signals.append("Clean network topology with normal node degree centrality")

        return {
            "network_mule_risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "mule_syndicate_detected": is_mule_syndicate,
            "cyclic_flow_detected": is_cyclic,
            "cycle_path": cycle_path,
            "smurfing_detected": smurf_info["is_smurfing"],
            "signals": signals[:4],
        }

    def get_network_topology(self, max_nodes: int = 50) -> Dict[str, Any]:
        """
        Exports graph nodes & edges formatted for D3/Cytoscape/Canvas visualization in React.
        """
        nodes_dict = {}
        edges_list = []

        for sender, transfers in list(self.adj.items())[:max_nodes]:
            sender_type = "mule" if sender in self.flagged_mule_nodes else ("merchant" if "MERCHANT" in sender else "account")
            if sender not in nodes_dict:
                nodes_dict[sender] = {"id": sender, "label": sender, "type": sender_type, "is_mule": sender in self.flagged_mule_nodes}

            for receiver, amount, ts, txid in transfers[-10:]:
                recv_type = "mule" if receiver in self.flagged_mule_nodes else ("merchant" if "MERCHANT" in receiver else "account")
                if receiver not in nodes_dict:
                    nodes_dict[receiver] = {"id": receiver, "label": receiver, "type": recv_type, "is_mule": receiver in self.flagged_mule_nodes}

                edges_list.append({
                    "id": txid,
                    "source": sender,
                    "target": receiver,
                    "amount": amount,
                    "is_suspicious": sender in self.flagged_mule_nodes or receiver in self.flagged_mule_nodes,
                })

        return {
            "nodes": list(nodes_dict.values()),
            "edges": edges_list[:100],
            "total_nodes": len(nodes_dict),
            "total_edges": len(edges_list),
            "flagged_mules_count": len(self.flagged_mule_nodes),
        }


# Global singleton
gnn_analyzer = GraphNetworkAnalyzer()
