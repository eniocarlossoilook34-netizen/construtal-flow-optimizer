"""Phase 2 optimization tests."""

import pytest
import numpy as np
from construtal_flow.network import Network
from construtal_flow.optimization import (
    ObjectiveFunction,
    ObjectiveType,
    ConstraintHandler,
    RandomSearch,
    GradientDescent,
    EvolutionaryAlgorithm,
    SimulatedAnnealing,
)


class TestObjectiveFunction:
    """Test objective function evaluation."""

    def test_objective_evaluation(self):
        """Test objective function works."""
        net = Network(num_nodes=3, source_id=0, sink_id=2)
        net.add_channel(0, 1, length=1.0, radius=0.05)
        net.add_channel(1, 2, length=1.0, radius=0.05)

        obj = ObjectiveFunction(net, ObjectiveType.RESISTANCE)

        radii = np.array([0.05, 0.05])
        J = obj.evaluate(radii)

        assert J > 0, "Objective should be positive"
        assert isinstance(J, float), "Objective should be float"

    def test_objective_decreases_with_radius(self):
        """Larger radii should give lower resistance."""
        net = Network(num_nodes=2, source_id=0, sink_id=1)
        net.add_channel(0, 1, length=1.0, radius=0.05)

        obj = ObjectiveFunction(net, ObjectiveType.RESISTANCE)

        # Small radius
        J1 = obj.evaluate(np.array([0.02]))

        # Large radius
        J2 = obj.evaluate(np.array([0.08]))

        assert J2 < J1, "Larger radius should give smaller resistance"

    def test_dissipation_objective(self):
        """Test dissipation objective."""
        net = Network(num_nodes=2, source_id=0, sink_id=1)
        net.add_channel(0, 1, length=1.0, radius=0.05)

        obj = ObjectiveFunction(net, ObjectiveType.DISSIPATION)
        J = obj.evaluate(np.array([0.05]))

        assert J > 0, "Dissipation should be positive"


class TestConstraintHandler:
    """Test constraint handling."""

    def test_feasibility_check(self):
        """Test feasibility checking."""
        net = Network(num_nodes=2, source_id=0, sink_id=1)
        net.add_channel(0, 1, length=1.0, radius=0.05)

        constraints = ConstraintHandler(net, volume_budget=1.0)

        # Feasible
        radii_feas = np.array([0.05])
        assert constraints.is_feasible(radii_feas)

        # Too large
        radii_infeas = np.array([10.0])
        assert not constraints.is_feasible(radii_infeas)

    def test_projection(self):
        """Test projection to feasible region."""
        net = Network(num_nodes=2, source_id=0, sink_id=1)
        net.add_channel(0, 1, length=1.0, radius=0.05)

        constraints = ConstraintHandler(net, volume_budget=1.0)

        # Infeasible radii
        radii_infeas = np.array([10.0])

        # Project
        radii_proj = constraints.project_to_feasible(radii_infeas)

        # Check feasibility
        assert constraints.is_feasible(radii_proj)

    def test_volume_constraint(self):
        """Test volume constraint enforcement."""
        net = Network(num_nodes=2, source_id=0, sink_id=1)
        net.add_channel(0, 1, length=1.0, radius=0.05)

        volume_budget = 0.1
        constraints = ConstraintHandler(net, volume_budget=volume_budget)

        radii = constraints.random_feasible()
        volume = constraints.get_volume(radii)

        assert volume <= volume_budget * 1.01, "Volume should respect budget (with tolerance)"


class TestOptimizers:
    """Test all optimizer implementations."""

    def setup_method(self):
        """Setup test network."""
        self.net = Network(num_nodes=3, source_id=0, sink_id=2)
        self.net.add_channel(0, 1, length=1.0, radius=0.05)
        self.net.add_channel(1, 2, length=1.0, radius=0.05)

    def test_random_search_converges(self):
        """Test random search."""
        opt = RandomSearch(
            self.net,
            obj_type=ObjectiveType.RESISTANCE,
            volume_budget=1.0,
            max_iterations=50,
            seed=42,
        )

        result = opt.optimize()

        assert result.best_objective > 0
        assert result.improvement >= 0
        assert result.converged
        assert len(result.history_best) == 50

    def test_gradient_descent_converges(self):
        """Test gradient descent."""
        opt = GradientDescent(
            self.net,
            obj_type=ObjectiveType.RESISTANCE,
            volume_budget=1.0,
            max_iterations=50,
            seed=42,
            learning_rate=0.01,
        )

        result = opt.optimize()

        assert result.best_objective > 0
        assert result.converged
        assert len(result.history_best) == 50

    def test_evolutionary_converges(self):
        """Test evolutionary algorithm."""
        opt = EvolutionaryAlgorithm(
            self.net,
            obj_type=ObjectiveType.RESISTANCE,
            volume_budget=1.0,
            max_iterations=50,
            seed=42,
            population_size=10,
        )

        result = opt.optimize()

        assert result.best_objective > 0
        assert result.converged
        assert len(result.history_best) == 50

    def test_simulated_annealing_converges(self):
        """Test simulated annealing."""
        opt = SimulatedAnnealing(
            self.net,
            obj_type=ObjectiveType.RESISTANCE,
            volume_budget=1.0,
            max_iterations=50,
            seed=42,
        )

        result = opt.optimize()

        assert result.best_objective > 0
        assert result.converged
        assert len(result.history_best) == 50

    def test_improvement_tracking(self):
        """Test that improvement is tracked correctly."""
        opt = RandomSearch(
            self.net,
            obj_type=ObjectiveType.RESISTANCE,
            volume_budget=1.0,
            max_iterations=50,
            seed=42,
        )

        result = opt.optimize()

        # Improvement should be between -1 and 1
        assert -1 <= result.improvement <= 1
        assert 0 <= result.improvement_percent <= 100

    def test_reproducibility(self):
        """Test that results are reproducible with same seed."""
        opt1 = RandomSearch(
            self.net,
            obj_type=ObjectiveType.RESISTANCE,
            max_iterations=30,
            seed=123,
        )
        result1 = opt1.optimize()

        opt2 = RandomSearch(
            self.net,
            obj_type=ObjectiveType.RESISTANCE,
            max_iterations=30,
            seed=123,
        )
        result2 = opt2.optimize()

        assert abs(result1.best_objective - result2.best_objective) < 1e-10


class TestAlgorithmComparison:
    """Compare algorithm performance."""

    def test_algorithms_on_series_network(self):
        """Run all algorithms on series network."""
        net = Network(num_nodes=4, source_id=0, sink_id=3)
        net.add_channel(0, 1, length=1.0, radius=0.05)
        net.add_channel(1, 2, length=1.0, radius=0.05)
        net.add_channel(2, 3, length=1.0, radius=0.05)

        algorithms = [
            RandomSearch,
            GradientDescent,
            EvolutionaryAlgorithm,
            SimulatedAnnealing,
        ]

        results = []

        for algo_class in algorithms:
            opt = algo_class(net, max_iterations=30, seed=42)
            result = opt.optimize()
            results.append(result)

        # All should improve
        for result in results:
            assert result.improvement > -0.1, "Should not get much worse"

        # At least one should improve
        assert max(r.improvement for r in results) > 0.05


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
