"""Topological mutations: operations that modify network structure."""

from typing import Tuple, List, Optional
import numpy as np
from construtal_flow.network import Network
from construtal_flow.physics.constants import Constraints


class TopologyMutator:
    """Generates topological mutations (add, remove, redirect channels)."""

    def __init__(self, network: Network):
        """
        Initialize mutator for a network.

        Args:
            network: Network instance
        """
        self.network = network

    def get_candidate_edges(self) -> List[Tuple[int, int]]:
        """
        Get all possible edges that could be added (not yet in network).

        Returns:
            List of (node_i, node_j) tuples that could be connected
        """
        existing_edges = set()
        for ch in self.network.channels.values():
            existing_edges.add((ch.node_from, ch.node_to))

        candidates = []
        for i in range(self.network.num_nodes):
            for j in range(self.network.num_nodes):
                if i != j and (i, j) not in existing_edges:
                    candidates.append((i, j))

        return candidates

    def add_channel(
        self,
        node_from: int,
        node_to: int,
        length: float,
        radius: Optional[float] = None,
    ) -> bool:
        """
        Add a new channel to the network.

        Args:
            node_from: Source node
            node_to: Target node
            length: Channel length
            radius: Channel radius (default: 0.05 m)

        Returns:
            True if successful, False if violates constraints
        """
        if radius is None:
            radius = 0.05

        # Check bounds
        if not (Constraints.r_min <= radius <= Constraints.r_max):
            return False
        if not (Constraints.L_min <= length <= Constraints.L_max):
            return False

        # Check volume budget
        new_volume = np.pi * radius**2 * length
        total_volume = self.network.total_volume() + new_volume
        if total_volume > Constraints.V_total:
            return False

        # Add channel
        self.network.add_channel(node_from, node_to, length, radius)
        return True

    def remove_channel(self, channel_id: int) -> bool:
        """
        Remove a channel from the network.

        Must not disconnect network (connectivity constraint).

        Args:
            channel_id: ID of channel to remove

        Returns:
            True if successful, False if would disconnect network
        """
        if channel_id not in self.network.channels:
            return False

        # Temporarily remove
        channel = self.network.channels.pop(channel_id)

        # Check connectivity
        connected = self.network.check_connectivity()

        if not connected:
            # Restore and fail
            self.network.channels[channel_id] = channel
            return False

        # Successfully removed
        return True

    def redirect_channel(
        self,
        channel_id: int,
        new_target: int,
    ) -> bool:
        """
        Redirect a channel to a different target node.

        Keeps source node, length, radius fixed; only changes target.

        Args:
            channel_id: Channel to redirect
            new_target: New target node

        Returns:
            True if successful
        """
        if channel_id not in self.network.channels:
            return False

        channel = self.network.channels[channel_id]

        if new_target == channel.node_to:
            return False  # No change

        if new_target == channel.node_from:
            return False  # Would create self-loop

        # Save old target
        old_target = channel.node_to

        # Try redirect
        channel.node_to = new_target

        # Check connectivity
        connected = self.network.check_connectivity()

        if not connected:
            # Restore
            channel.node_to = old_target
            return False

        return True

    def add_intermediate_node(
        self,
        channel_id: int,
        new_node_id: Optional[int] = None,
    ) -> bool:
        """
        Split a channel by inserting an intermediate node.

        Creates: i --[R1]-- new_node --[R2]-- j
        instead of: i --[R]-- j

        Args:
            channel_id: Channel to split
            new_node_id: ID for new node (default: next available)

        Returns:
            True if successful
        """
        if channel_id not in self.network.channels:
            return False

        channel = self.network.channels[channel_id]

        # Determine new node ID
        if new_node_id is None:
            new_node_id = self.network.num_nodes

        # Check node doesn't exist
        if new_node_id < self.network.num_nodes:
            return False

        # Split channel into two: each gets half the length, original radius
        L1 = channel.length / 2
        L2 = channel.length / 2
        r = channel.radius

        # Remove original channel
        removed = self.remove_channel(channel_id)
        if not removed:
            return False

        # Increase node count
        self.network.num_nodes += 1
        self.network.adjacency[new_node_id] = []

        # Add two new channels
        self.add_channel(channel.node_from, new_node_id, L1, r)
        self.add_channel(new_node_id, channel.node_to, L2, r)

        return True

    def get_random_mutation(self, random_state: np.random.RandomState = None) -> Optional[str]:
        """
        Return a random mutation type.

        Args:
            random_state: NumPy random state

        Returns:
            One of: 'add', 'remove', 'redirect' or None
        """
        if random_state is None:
            random_state = np.random.RandomState()

        # Try to add channel if possible
        candidates = self.get_candidate_edges()
        can_add = len(candidates) > 0

        # Try to remove channel if possible (keep at least 1)
        can_remove = len(self.network.channels) > 1

        # Try to redirect if possible
        can_redirect = len(self.network.channels) > 0

        possible = []
        if can_add:
            possible.append("add")
        if can_remove:
            possible.append("remove")
        if can_redirect:
            possible.append("redirect")

        if not possible:
            return None

        return random_state.choice(possible)

    def apply_random_mutation(
        self,
        mutation_type: str,
        random_state: np.random.RandomState = None,
    ) -> bool:
        """
        Apply a random mutation of given type.

        Args:
            mutation_type: 'add', 'remove', or 'redirect'
            random_state: NumPy random state

        Returns:
            True if mutation applied successfully
        """
        if random_state is None:
            random_state = np.random.RandomState()

        if mutation_type == "add":
            candidates = self.get_candidate_edges()
            if not candidates:
                return False
            node_from, node_to = candidates[random_state.randint(len(candidates))]
            length = random_state.uniform(Constraints.L_min, Constraints.L_max)
            radius = random_state.uniform(Constraints.r_min, Constraints.r_max)
            return self.add_channel(node_from, node_to, length, radius)

        elif mutation_type == "remove":
            if not self.network.channels:
                return False
            ch_id = random_state.choice(list(self.network.channels.keys()))
            return self.remove_channel(ch_id)

        elif mutation_type == "redirect":
            if not self.network.channels:
                return False
            ch_id = random_state.choice(list(self.network.channels.keys()))
            channel = self.network.channels[ch_id]

            # Random target (different from current)
            possible_targets = [
                n for n in range(self.network.num_nodes)
                if n != channel.node_from and n != channel.node_to
            ]
            if not possible_targets:
                return False

            new_target = random_state.choice(possible_targets)
            return self.redirect_channel(ch_id, new_target)

        else:
            return False
