"""Network class: Directed graph representation of hydraulic networks."""

from typing import List, Dict, Tuple, Optional
import numpy as np
from construtal_flow.physics import Channel, FluidProperties
from construtal_flow.physics.constants import Constraints


class Network:
    """
    Directed graph representing a laminar hydraulic flow network.

    Nodes: junctions
    Edges: cylindrical channels
    Flow direction: from source to sink
    """

    def __init__(
        self,
        num_nodes: int,
        source_id: int,
        sink_id: int,
        fluid: FluidProperties = None,
    ):
        """
        Initialize an empty network.

        Args:
            num_nodes: Total number of nodes
            source_id: Index of source node (inlet)
            sink_id: Index of sink node (outlet)
            fluid: FluidProperties instance
        """
        self.num_nodes = num_nodes
        self.source_id = source_id
        self.sink_id = sink_id
        self.fluid = fluid or FluidProperties()

        if source_id == sink_id:
            raise ValueError("Source and sink must be different nodes")
        if not (0 <= source_id < num_nodes):
            raise ValueError(f"Invalid source_id: {source_id}")
        if not (0 <= sink_id < num_nodes):
            raise ValueError(f"Invalid sink_id: {sink_id}")

        # Network structure
        self.channels: Dict[int, Channel] = {}
        self.adjacency: Dict[int, List[Tuple[int, int]]] = {
            i: [] for i in range(num_nodes)
        }
        self.next_channel_id = 0

        # Node pressures (computed by solver)
        self.pressures = np.zeros(num_nodes)

        # Boundary conditions
        self.Q_in = 1.0  # Inlet flow rate (m³/s)
        self.P_ref = 0.0  # Reference pressure at sink (Pa)

    def add_channel(
        self,
        node_from: int,
        node_to: int,
        length: float,
        radius: float,
    ) -> int:
        """
        Add a directed channel to the network.

        Args:
            node_from: Source node
            node_to: Target node
            length: Channel length (m)
            radius: Channel radius (m)

        Returns:
            Channel ID
        """
        if not (0 <= node_from < self.num_nodes):
            raise ValueError(f"Invalid node_from: {node_from}")
        if not (0 <= node_to < self.num_nodes):
            raise ValueError(f"Invalid node_to: {node_to}")

        channel = Channel(
            self.next_channel_id, node_from, node_to, length, radius, self.fluid
        )
        self.channels[channel.id] = channel
        self.adjacency[node_from].append((node_to, channel.id))

        self.next_channel_id += 1
        return channel.id

    def get_channel(self, channel_id: int) -> Channel:
        """Retrieve a channel by ID."""
        if channel_id not in self.channels:
            raise ValueError(f"Channel {channel_id} not found")
        return self.channels[channel_id]

    def get_incoming_channels(self, node_id: int) -> List[Channel]:
        """Get all channels flowing into a node."""
        return [
            self.channels[ch_id]
            for ch_id in self.channels
            if self.channels[ch_id].node_to == node_id
        ]

    def get_outgoing_channels(self, node_id: int) -> List[Channel]:
        """Get all channels flowing out of a node."""
        return [
            self.channels[ch_id]
            for ch_id in self.channels
            if self.channels[ch_id].node_from == node_id
        ]

    def check_connectivity(self) -> bool:
        """Check if network is connected (simple path exists from source to sink)."""
        if not self.channels:
            return False

        visited = set()
        queue = [self.source_id]

        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)

            if node == self.sink_id:
                return True

            for next_node, _ in self.adjacency[node]:
                if next_node not in visited:
                    queue.append(next_node)

        return False

    def total_volume(self) -> float:
        """Total volume of all channels."""
        return sum(ch.volume for ch in self.channels.values())

    def total_resistance_series(self) -> float:
        """
        Compute total resistance assuming all channels in series.

        Used as analytical reference for validation.
        """
        return sum(ch.resistance for ch in self.channels.values())

    def total_resistance_parallel(self) -> float:
        """
        Compute total resistance assuming all channels in parallel.

        Used as analytical reference for validation.
        """
        if not self.channels:
            return float("inf")
        inv_sum = sum(1.0 / ch.resistance for ch in self.channels.values())
        if inv_sum == 0:
            return float("inf")
        return 1.0 / inv_sum

    def get_network_metrics(self) -> Dict[str, float]:
        """
        Compute network-level metrics.

        Returns dict with:
            - R_eff: Effective resistance
            - P_drop: Pressure drop source to sink
            - P_diss_total: Total dissipated power
            - volume: Total channel volume
            - avg_velocity: Average velocity across channels
        """
        if not self.channels:
            return {
                "R_eff": float("inf"),
                "P_drop": 0.0,
                "P_diss_total": 0.0,
                "volume": 0.0,
                "avg_velocity": 0.0,
            }

        P_drop = self.pressures[self.source_id] - self.pressures[self.sink_id]
        R_eff = P_drop / self.Q_in if self.Q_in > 0 else float("inf")

        P_diss_total = sum(ch.compute_dissipated_power(ch.Q)
                          for ch in self.channels.values() if ch.Q is not None)
        volume = self.total_volume()

        velocities = [
            ch.compute_velocity(ch.Q)
            for ch in self.channels.values()
            if ch.Q is not None and ch.Q > 0
        ]
        avg_velocity = np.mean(velocities) if velocities else 0.0

        return {
            "R_eff": R_eff,
            "P_drop": P_drop,
            "P_diss_total": P_diss_total,
            "volume": volume,
            "avg_velocity": avg_velocity,
        }

    def reset_flows(self):
        """Reset all flow rates and pressures to None/zero."""
        for ch in self.channels.values():
            ch.Q = None
            ch.delta_P = None
        self.pressures = np.zeros(self.num_nodes)

    def __repr__(self) -> str:
        return (
            f"Network(nodes={self.num_nodes}, channels={len(self.channels)}, "
            f"source={self.source_id}, sink={self.sink_id})"
        )
