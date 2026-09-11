"""Constructal Law implementation: identify flow bottlenecks and guide evolution."""

from typing import List, Tuple
import numpy as np
from construtal_flow.network import Network


class ConstructalIndicator:
    """Identifies flow bottlenecks using Constructal principles."""

    def __init__(self, network: Network):
        """
        Initialize indicator.

        Args:
            network: Network instance (must be solved)
        """
        self.network = network

    def get_dissipation_per_channel(self) -> dict:
        """
        Compute dissipation (resistance × flow²) for each channel.

        Returns:
            Dictionary: channel_id → dissipation (W)
        """
        dissipation = {}

        for ch_id, channel in self.network.channels.items():
            if channel.Q is not None:
                P = channel.compute_dissipated_power(channel.Q)
                dissipation[ch_id] = P
            else:
                dissipation[ch_id] = 0.0

        return dissipation

    def get_hot_channels(self, percentile: float = 75.0) -> List[int]:
        """
        Identify "hot channels" (high dissipation).

        These are bottlenecks where adding parallel paths could help.

        Args:
            percentile: Threshold percentile (default: 75th)

        Returns:
            List of hot channel IDs
        """
        dissipation = self.get_dissipation_per_channel()

        if not dissipation:
            return []

        values = list(dissipation.values())
        threshold = np.percentile(values, percentile)

        hot_channels = [ch_id for ch_id, P in dissipation.items() if P >= threshold]

        return hot_channels

    def get_flow_path(self) -> List[int]:
        """
        Identify main flow path from source to sink.

        Uses flow magnitudes to identify primary path.

        Returns:
            List of node IDs forming main path
        """
        path = [self.network.source_id]
        current = self.network.source_id

        while current != self.network.sink_id:
            # Find outgoing channel with highest flow
            best_flow = 0
            best_next = None

            for next_node, ch_id in self.network.adjacency[current]:
                channel = self.network.channels[ch_id]
                if channel.Q is not None and channel.Q > best_flow:
                    best_flow = channel.Q
                    best_next = next_node

            if best_next is None:
                break  # Dead end (shouldn't happen if connected)

            path.append(best_next)
            current = best_next

            # Prevent infinite loops
            if len(path) > self.network.num_nodes:
                break

        return path

    def get_bifurcation_points(self) -> List[int]:
        """
        Identify nodes where flow splits significantly.

        Args:
            None

        Returns:
            List of node IDs with bifurcations
        """
        bifurcations = []

        for node_id in range(self.network.num_nodes):
            outgoing = self.network.get_outgoing_channels(node_id)

            if len(outgoing) <= 1:
                continue  # No bifurcation

            # Compute flow splits
            flows = [ch.Q for ch in outgoing if ch.Q is not None]

            if not flows:
                continue

            max_flow = max(flows)
            min_flow = min(flows)

            # Significant if flows differ substantially
            if max_flow > 0 and min_flow / max_flow < 0.5:
                bifurcations.append(node_id)

        return bifurcations

    def suggest_channel_to_remove(self) -> int:
        """
        Suggest a low-value channel for removal.

        Args:
            None

        Returns:
            Channel ID of candidate for removal
        """
        dissipation = self.get_dissipation_per_channel()

        if not dissipation:
            return None

        # Find channel with lowest dissipation
        return min(dissipation, key=dissipation.get)

    def suggest_parallel_path(self) -> Tuple[int, int]:
        """
        Suggest adding a parallel path to reduce bottleneck.

        Returns node pair that should be connected.

        Args:
            None

        Returns:
            (node_i, node_j) tuple for new channel, or (None, None)
        """
        hot = self.get_hot_channels(percentile=80.0)

        if not hot:
            return None, None

        # Get first hot channel
        ch_id = hot[0]
        channel = self.network.channels[ch_id]

        # Suggest parallel path by connecting same endpoints
        return channel.node_from, channel.node_to

    def print_analysis(self):
        """Print Constructal analysis."""
        print("\nConstructal Analysis:")

        # Dissipation
        dissipation = self.get_dissipation_per_channel()
        print(f"  Total dissipation: {sum(dissipation.values()):.4e} W")
        print(f"  Hot channels: {len(self.get_hot_channels())}")

        # Main path
        main_path = self.get_flow_path()
        print(f"  Main path: {' → '.join(str(n) for n in main_path)}")

        # Bifurcations
        bifurcations = self.get_bifurcation_points()
        print(f"  Bifurcation points: {bifurcations}")

        # Suggestions
        ch_remove = self.suggest_channel_to_remove()
        if ch_remove is not None:
            print(f"  Remove candidate: Channel {ch_remove}")

        ch_i, ch_j = self.suggest_parallel_path()
        if ch_i is not None:
            print(f"  Add parallel path: {ch_i} ↔ {ch_j}")
