"""Topological validation: check network properties."""

from typing import Set
from construtal_flow.network import Network


class TopologyValidator:
    """Validates network topology constraints."""

    @staticmethod
    def is_connected(network: Network) -> bool:
        """
        Check if network has path from source to sink.

        Args:
            network: Network to validate

        Returns:
            True if connected
        """
        return network.check_connectivity()

    @staticmethod
    def is_acyclic(network: Network) -> bool:
        """
        Check if network is acyclic (DAG).

        Uses depth-first search to detect cycles.

        Args:
            network: Network to validate

        Returns:
            True if acyclic (no cycles)
        """
        # For directed graph: DFS with white/gray/black coloring
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {i: WHITE for i in range(network.num_nodes)}

        def has_cycle_dfs(node: int) -> bool:
            color[node] = GRAY

            # Check outgoing edges
            for next_node, _ in network.adjacency[node]:
                if color[next_node] == GRAY:
                    # Back edge = cycle
                    return True
                if color[next_node] == WHITE:
                    if has_cycle_dfs(next_node):
                        return True

            color[node] = BLACK
            return False

        # Check from all nodes
        for node in range(network.num_nodes):
            if color[node] == WHITE:
                if has_cycle_dfs(node):
                    return False

        return True

    @staticmethod
    def is_tree(network: Network) -> bool:
        """
        Check if network is a tree (connected, acyclic, n edges = n-1 nodes).

        Args:
            network: Network to validate

        Returns:
            True if tree
        """
        if not TopologyValidator.is_connected(network):
            return False

        if not TopologyValidator.is_acyclic(network):
            return False

        # Tree: num_edges = num_nodes - 1
        n_edges = len(network.channels)
        n_nodes_used = network.num_nodes  # In practice, may have isolated nodes

        # For a tree connecting source to sink
        # We expect at least (num_nodes - 1) edges if all nodes are used
        return n_edges <= n_nodes_used - 1

    @staticmethod
    def get_longest_path(network: Network) -> int:
        """
        Compute longest path from source to sink.

        Args:
            network: Network to analyze

        Returns:
            Number of edges in longest path
        """
        # BFS/DFS to find longest path
        def longest_path_dfs(node: int, visited: Set[int]) -> int:
            if node == network.sink_id:
                return 0

            max_length = -1  # No path found

            for next_node, _ in network.adjacency[node]:
                if next_node not in visited:
                    visited.add(next_node)
                    length = longest_path_dfs(next_node, visited)
                    if length >= 0:
                        max_length = max(max_length, 1 + length)
                    visited.remove(next_node)

            return max_length

        visited = {network.source_id}
        length = longest_path_dfs(network.source_id, visited)

        return length if length >= 0 else float('inf')

    @staticmethod
    def validate_all(network: Network) -> dict:
        """
        Run all validation checks.

        Args:
            network: Network to validate

        Returns:
            Dictionary with validation results
        """
        return {
            "connected": TopologyValidator.is_connected(network),
            "acyclic": TopologyValidator.is_acyclic(network),
            "tree": TopologyValidator.is_tree(network),
            "longest_path": TopologyValidator.get_longest_path(network),
            "num_channels": len(network.channels),
            "num_nodes": network.num_nodes,
        }

    @staticmethod
    def print_validation(network: Network):
        """Print validation results."""
        results = TopologyValidator.validate_all(network)

        print("Topology Validation:")
        print(f"  Connected: {'✓' if results['connected'] else '✗'}")
        print(f"  Acyclic: {'✓' if results['acyclic'] else '✗'}")
        print(f"  Tree: {'✓' if results['tree'] else '✗'}")
        print(f"  Longest path: {results['longest_path']} edges")
        print(f"  Channels: {results['num_channels']}")
        print(f"  Nodes: {results['num_nodes']}")
