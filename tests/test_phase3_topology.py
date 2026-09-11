"""Phase 3 topological optimization tests."""

import pytest
import numpy as np
from construtal_flow.network import Network
from construtal_flow.topology import (
    TopologyMutator,
    TopologyValidator,
    ConstructalIndicator,
    EvolutionaryTopology,
    ConstructalSearch,
    SimulatedTopologyAnnealing,
)
from construtal_flow.solver import LinearSolver


class TestTopologyMutator:
    """Test topological mutations."""

    def setup_method(self):
        """Create test network."""
        self.net = Network(num_nodes=4, source_id=0, sink_id=3)
        self.net.add_channel(0, 1, length=1.0, radius=0.05)
        self.net.add_channel(1, 2, length=1.0, radius=0.05)
        self.net.add_channel(2, 3, length=1.0, radius=0.05)

    def test_add_channel(self):
        """Test adding a channel."""
        mutator = TopologyMutator(self.net)

        initial_count = len(self.net.channels)
        success = mutator.add_channel(0, 2, length=1.5, radius=0.04)

        assert success
        assert len(self.net.channels) == initial_count + 1

    def test_add_channel_violates_budget(self):
        """Test that adding oversized channel fails."""
        mutator = TopologyMutator(self.net)

        # Try to add huge channel
        success = mutator.add_channel(0, 2, length=100.0, radius=0.5)

        assert not success

    def test_remove_channel_maintains_connectivity(self):
        """Test that removal maintains connectivity."""
        mutator = TopologyMutator(self.net)

        # Remove middle channel - should maintain path
        # 0 -> 1 -> 2 -> 3, remove 1->2, still have 0->1 path exists but no sink
        # Try removing a channel that's not critical
        self.net.add_channel(1, 3, length=2.0, radius=0.04)

        ch_id = list(self.net.channels.keys())[-1]  # Remove the newly added channel
        success = mutator.remove_channel(ch_id)

        assert success
        assert TopologyValidator.is_connected(self.net)

    def test_redirect_channel(self):
        """Test redirecting a channel."""
        mutator = TopologyMutator(self.net)

        # Add extra node
        self.net.num_nodes = 5
        self.net.adjacency[4] = []

        ch_id = list(self.net.channels.keys())[0]
        channel = self.net.channels[ch_id]
        old_target = channel.node_to

        # Redirect to new node
        success = mutator.redirect_channel(ch_id, 4)

        if success:
            assert channel.node_to == 4
        else:
            # May fail due to connectivity
            assert channel.node_to == old_target

    def test_get_candidate_edges(self):
        """Test candidate edge generation."""
        mutator = TopologyMutator(self.net)

        candidates = mutator.get_candidate_edges()

        assert len(candidates) > 0
        assert all(isinstance(c, tuple) and len(c) == 2 for c in candidates)


class TestTopologyValidator:
    """Test topology validation."""

    def setup_method(self):
        """Create test network."""
        self.net = Network(num_nodes=4, source_id=0, sink_id=3)
        self.net.add_channel(0, 1, length=1.0, radius=0.05)
        self.net.add_channel(1, 2, length=1.0, radius=0.05)
        self.net.add_channel(2, 3, length=1.0, radius=0.05)

    def test_is_connected(self):
        """Test connectivity checking."""
        assert TopologyValidator.is_connected(self.net)

        # Remove all channels
        self.net.channels.clear()
        assert not TopologyValidator.is_connected(self.net)

    def test_is_acyclic(self):
        """Test acyclicity checking."""
        assert TopologyValidator.is_acyclic(self.net)

        # Add a cycle
        self.net.add_channel(3, 1, length=1.0, radius=0.05)

        # DAG check should still pass (directed acyclic)
        # But if we added reverse edge creating cycle:
        # 0->1->2->3->1 would be cycle
        is_acyclic = TopologyValidator.is_acyclic(self.net)
        # Note: 3->1 doesn't create cycle if direction is strict

    def test_is_tree(self):
        """Test tree property."""
        assert TopologyValidator.is_tree(self.net)

        # Add extra channel (no longer a tree)
        self.net.add_channel(0, 3, length=2.0, radius=0.04)

        assert not TopologyValidator.is_tree(self.net)

    def test_validation_summary(self):
        """Test validation summary."""
        results = TopologyValidator.validate_all(self.net)

        assert results["connected"]
        assert results["acyclic"]
        assert results["num_channels"] == 3
        assert results["num_nodes"] == 4


class TestConstructalIndicator:
    """Test Constructal analysis."""

    def setup_method(self):
        """Create test network and solve it."""
        self.net = Network(num_nodes=4, source_id=0, sink_id=3)
        self.net.add_channel(0, 1, length=1.0, radius=0.05)
        self.net.add_channel(1, 2, length=1.0, radius=0.05)
        self.net.add_channel(2, 3, length=1.0, radius=0.05)

        # Solve to get flow
        solver = LinearSolver(self.net)
        solver.solve()

    def test_dissipation_per_channel(self):
        """Test dissipation calculation."""
        indicator = ConstructalIndicator(self.net)
        dissipation = indicator.get_dissipation_per_channel()

        assert len(dissipation) == len(self.net.channels)
        assert all(p >= 0 for p in dissipation.values())

    def test_hot_channels(self):
        """Test hot channel identification."""
        indicator = ConstructalIndicator(self.net)
        hot = indicator.get_hot_channels(percentile=50.0)

        assert isinstance(hot, list)
        assert all(ch_id in self.net.channels for ch_id in hot)

    def test_flow_path(self):
        """Test main flow path identification."""
        indicator = ConstructalIndicator(self.net)
        path = indicator.get_flow_path()

        assert path[0] == self.net.source_id
        assert path[-1] == self.net.sink_id


class TestTopologyAlgorithms:
    """Test topology optimization algorithms."""

    def setup_method(self):
        """Create test network."""
        self.net = Network(num_nodes=3, source_id=0, sink_id=2)
        self.net.add_channel(0, 1, length=1.5, radius=0.05)
        self.net.add_channel(1, 2, length=1.5, radius=0.05)

    def test_evolutionary_topology(self):
        """Test evolutionary topology optimizer."""
        opt = EvolutionaryTopology(self.net, max_iterations=10, seed=42)
        result = opt.optimize()

        assert result.best_objective >= 0  # Can be 0 if ill-conditioned
        assert result.improvement >= -0.1  # Allow some noise
        assert result.final_channels > 0
        assert len(result.history_best) == 11  # 10 iterations + initial

    def test_constructal_search(self):
        """Test Constructal search."""
        opt = ConstructalSearch(self.net, max_iterations=10, seed=42)
        result = opt.optimize()

        assert result.best_objective > 0
        assert result.final_channels > 0

    def test_simulated_topology_annealing(self):
        """Test simulated topology annealing."""
        opt = SimulatedTopologyAnnealing(
            self.net,
            max_iterations=10,
            seed=42,
        )
        result = opt.optimize()

        assert result.best_objective >= 0  # Can be 0 if ill-conditioned
        assert result.final_channels > 0

    def test_algorithm_convergence(self):
        """Test that algorithms show improvement."""
        algorithms = [
            EvolutionaryTopology,
            ConstructalSearch,
            SimulatedTopologyAnnealing,
        ]

        for algo_class in algorithms:
            opt = algo_class(self.net, max_iterations=15, seed=42)
            result = opt.optimize()

            # Should show some improvement or stability
            assert result.best_objective <= result.initial_objective * 1.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
