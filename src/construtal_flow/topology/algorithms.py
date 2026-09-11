"""Topological optimization algorithms."""

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
from construtal_flow.network import Network
from construtal_flow.solver import LinearSolver
from construtal_flow.optimization import GradientDescent, ObjectiveType
from .mutations import TopologyMutator
from .validation import TopologyValidator
from .constructal import ConstructalIndicator


@dataclass
class TopologyResult:
    """Result of topology optimization."""

    best_network: Network
    best_objective: float
    initial_objective: float
    improvement: float
    generations: int
    final_channels: int
    final_nodes: int
    history_best: List[float]
    history_channels: List[int]


class EvolutionaryTopology:
    """Evolutionary algorithm for topological optimization."""

    def __init__(
        self,
        network: Network,
        max_iterations: int = 50,
        seed: int = None,
    ):
        """
        Initialize evolutionary topology optimizer.

        Args:
            network: Initial network
            max_iterations: Maximum generations
            seed: Random seed
        """
        self.network = network
        self.max_iterations = max_iterations
        self.seed = seed

        if seed is not None:
            np.random.seed(seed)

        self.rng = np.random.RandomState(seed)

    def optimize(self) -> TopologyResult:
        """Run evolutionary topology optimization."""
        solver = LinearSolver(self.network)

        # Initial evaluation
        solver.solve()
        initial_obj = self.network.get_network_metrics()["R_eff"]
        best_obj = initial_obj

        history_best = [best_obj]
        history_channels = [len(self.network.channels)]

        best_network = self._copy_network(self.network)

        for gen in range(self.max_iterations):
            # Mutate topology
            mutator = TopologyMutator(self.network)
            mutation_type = mutator.get_random_mutation(self.rng)

            if mutation_type:
                mutator.apply_random_mutation(mutation_type, self.rng)

            # Validate
            if not TopologyValidator.is_connected(self.network):
                # Restore to best
                self.network = self._copy_network(best_network)
                continue

            # Optimize radii (Phase 2)
            opt = GradientDescent(
                self.network,
                max_iterations=20,
                learning_rate=0.01,
                seed=self.seed + gen if self.seed else None,
            )
            opt.optimize()

            # Evaluate
            solver.solve()
            metrics = self.network.get_network_metrics()
            current_obj = metrics["R_eff"]

            # Track best
            if current_obj < best_obj:
                best_obj = current_obj
                best_network = self._copy_network(self.network)

            history_best.append(best_obj)
            history_channels.append(len(self.network.channels))

        improvement = (initial_obj - best_obj) / initial_obj

        return TopologyResult(
            best_network=best_network,
            best_objective=best_obj,
            initial_objective=initial_obj,
            improvement=improvement,
            generations=self.max_iterations,
            final_channels=len(best_network.channels),
            final_nodes=best_network.num_nodes,
            history_best=history_best,
            history_channels=history_channels,
        )

    @staticmethod
    def _copy_network(network: Network) -> Network:
        """Create deep copy of network."""
        net_copy = Network(
            num_nodes=network.num_nodes,
            source_id=network.source_id,
            sink_id=network.sink_id,
            fluid=network.fluid,
        )

        for ch in network.channels.values():
            net_copy.add_channel(ch.node_from, ch.node_to, ch.length, ch.radius)

        return net_copy


class ConstructalSearch:
    """Greedy algorithm guided by Constructal principles."""

    def __init__(
        self,
        network: Network,
        max_iterations: int = 50,
        seed: int = None,
    ):
        """
        Initialize Constructal search.

        Args:
            network: Initial network
            max_iterations: Maximum iterations
            seed: Random seed
        """
        self.network = network
        self.max_iterations = max_iterations
        self.seed = seed

        if seed is not None:
            np.random.seed(seed)

        self.rng = np.random.RandomState(seed)

    def optimize(self) -> TopologyResult:
        """Run Constructal-guided optimization."""
        solver = LinearSolver(self.network)
        solver.solve()

        initial_obj = self.network.get_network_metrics()["R_eff"]
        best_obj = initial_obj

        history_best = [best_obj]
        history_channels = [len(self.network.channels)]

        best_network = EvolutionaryTopology._copy_network(self.network)

        for gen in range(self.max_iterations):
            # Constructal analysis
            indicator = ConstructalIndicator(self.network)

            # Try to add parallel path to bottleneck
            node_i, node_j = indicator.suggest_parallel_path()

            if node_i is not None:
                mutator = TopologyMutator(self.network)
                length = self.rng.uniform(0.5, 2.0)
                radius = self.rng.uniform(0.03, 0.07)

                mutator.add_channel(node_i, node_j, length, radius)

            # Optimize radii
            opt = GradientDescent(
                self.network,
                max_iterations=20,
                learning_rate=0.01,
                seed=self.seed + gen if self.seed else None,
            )
            opt.optimize()

            # Evaluate
            solver.solve()
            metrics = self.network.get_network_metrics()
            current_obj = metrics["R_eff"]

            # Track best
            if current_obj < best_obj:
                best_obj = current_obj
                best_network = EvolutionaryTopology._copy_network(self.network)
            else:
                # No improvement: revert to best
                self.network = EvolutionaryTopology._copy_network(best_network)

            history_best.append(best_obj)
            history_channels.append(len(best_network.channels))

        improvement = (initial_obj - best_obj) / initial_obj

        return TopologyResult(
            best_network=best_network,
            best_objective=best_obj,
            initial_objective=initial_obj,
            improvement=improvement,
            generations=self.max_iterations,
            final_channels=len(best_network.channels),
            final_nodes=best_network.num_nodes,
            history_best=history_best,
            history_channels=history_channels,
        )


class SimulatedTopologyAnnealing:
    """Simulated annealing for topology space."""

    def __init__(
        self,
        network: Network,
        max_iterations: int = 50,
        initial_temperature: float = 1.0,
        cooling_rate: float = 0.95,
        seed: int = None,
    ):
        """
        Initialize simulated annealing.

        Args:
            network: Initial network
            max_iterations: Maximum iterations
            initial_temperature: Starting temperature
            cooling_rate: Cooling schedule
            seed: Random seed
        """
        self.network = network
        self.max_iterations = max_iterations
        self.initial_temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.seed = seed

        if seed is not None:
            np.random.seed(seed)

        self.rng = np.random.RandomState(seed)

    def optimize(self) -> TopologyResult:
        """Run simulated annealing on topology."""
        solver = LinearSolver(self.network)
        solver.solve()

        initial_obj = self.network.get_network_metrics()["R_eff"]
        current_obj = initial_obj
        best_obj = initial_obj

        history_best = [best_obj]
        history_channels = [len(self.network.channels)]

        best_network = EvolutionaryTopology._copy_network(self.network)
        current_network = EvolutionaryTopology._copy_network(self.network)

        temperature = self.initial_temperature

        for gen in range(self.max_iterations):
            # Random mutation
            mutator = TopologyMutator(current_network)
            mutation_type = mutator.get_random_mutation(self.rng)

            if mutation_type:
                mutator.apply_random_mutation(mutation_type, self.rng)

            # Check validity
            if not TopologyValidator.is_connected(current_network):
                # Reject
                current_network = EvolutionaryTopology._copy_network(best_network)
                temperature *= self.cooling_rate
                continue

            # Optimize radii
            opt = GradientDescent(
                current_network,
                max_iterations=20,
                learning_rate=0.01,
                seed=self.seed + gen if self.seed else None,
            )
            opt.optimize()

            # Evaluate
            solver_temp = LinearSolver(current_network)
            solver_temp.solve()
            metrics = current_network.get_network_metrics()
            neighbor_obj = metrics["R_eff"]

            # Metropolis criterion
            delta_J = neighbor_obj - current_obj
            if delta_J < 0 or self.rng.rand() < np.exp(-delta_J / max(temperature, 1e-10)):
                current_obj = neighbor_obj

                # Update best if better
                if current_obj < best_obj:
                    best_obj = current_obj
                    best_network = EvolutionaryTopology._copy_network(current_network)
            else:
                # Reject: restore
                current_network = EvolutionaryTopology._copy_network(best_network)

            temperature *= self.cooling_rate

            history_best.append(best_obj)
            history_channels.append(len(best_network.channels))

        improvement = (initial_obj - best_obj) / initial_obj

        return TopologyResult(
            best_network=best_network,
            best_objective=best_obj,
            initial_objective=initial_obj,
            improvement=improvement,
            generations=self.max_iterations,
            final_channels=len(best_network.channels),
            final_nodes=best_network.num_nodes,
            history_best=history_best,
            history_channels=history_channels,
        )
