"""Multi-objective Simulated Annealing using weight vector scalarization."""

from dataclasses import dataclass
from typing import List
import numpy as np
from construtal_flow.network import Network
from construtal_flow.topology import TopologyMutator
from construtal_flow.optimization import GradientDescent
from .objectives import ObjectiveSet, ParetoPoint
from .pareto import ParetoFrontier


@dataclass
class MultiObjSAResult:
    """Result from multi-objective SA."""

    pareto_frontier: ParetoFrontier
    generation: int
    evaluations: int
    history_frontier_size: List[int]


class MultiObjectiveSimulatedAnnealing:
    """Multi-objective SA using scalarization with varying weights."""

    def __init__(
        self,
        network: Network,
        num_weight_vectors: int = 10,
        iterations_per_vector: int = 30,
        initial_temperature: float = 1.0,
        cooling_rate: float = 0.95,
        seed: int = None,
    ):
        """
        Initialize multi-objective SA.

        Args:
            network: Initial network
            num_weight_vectors: Number of weight vectors to explore
            iterations_per_vector: Iterations per weight vector
            initial_temperature: Initial temperature
            cooling_rate: Cooling schedule
            seed: Random seed
        """
        self.network = network
        self.num_weight_vectors = num_weight_vectors
        self.iterations_per_vector = iterations_per_vector
        self.initial_temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.seed = seed

        if seed is not None:
            np.random.seed(seed)

        self.rng = np.random.RandomState(seed)
        self.pareto_frontier = ParetoFrontier()
        self.evaluations = 0

    def optimize(self) -> MultiObjSAResult:
        """Run multi-objective SA with varying weights."""
        history_frontier_size = []

        # Generate weight vectors (uniformly sampled on simplex)
        weight_vectors = self._generate_weight_vectors()

        for w_idx, weights in enumerate(weight_vectors):
            # Run SA with this weight vector
            self._run_sa_with_weights(weights)

            history_frontier_size.append(self.pareto_frontier.size())

        return MultiObjSAResult(
            pareto_frontier=self.pareto_frontier,
            generation=self.num_weight_vectors,
            evaluations=self.evaluations,
            history_frontier_size=history_frontier_size,
        )

    def _generate_weight_vectors(self) -> List[np.ndarray]:
        """Generate weight vectors for Chebyshev scalarization."""
        vectors = []

        for i in range(self.num_weight_vectors):
            # Simple: vary weights linearly
            w1 = i / (self.num_weight_vectors - 1)  # R_eff weight
            w2 = 1 - w1  # P_diss weight
            w3 = 0.1  # Volume weight (always important)
            w4 = 0.05  # Complexity weight (less important)

            weights = np.array([w1, w2, w3, w4])
            weights = weights / np.sum(weights)  # Normalize

            vectors.append(weights)

        return vectors

    def _run_sa_with_weights(self, weights: np.ndarray):
        """Run simulated annealing with a fixed weight vector."""
        current_net = self._copy_network(self.network)
        obj_set = ObjectiveSet(current_net)
        current_objectives = obj_set.compute_objective_vector()
        current_J = ObjectiveSet.scalarize(current_objectives, weights)

        temperature = self.initial_temperature

        for _ in range(self.iterations_per_vector):
            # Mutate topology
            mutator = TopologyMutator(current_net)
            mutation_type = mutator.get_random_mutation(self.rng)

            if mutation_type:
                mutator.apply_random_mutation(mutation_type, self.rng)

            # Optimize radii
            opt = GradientDescent(
                current_net,
                max_iterations=10,
                learning_rate=0.01,
                seed=self.seed,
            )
            opt.optimize()

            # Evaluate
            obj_set = ObjectiveSet(current_net)
            neighbor_objectives = obj_set.compute_objective_vector()
            neighbor_J = ObjectiveSet.scalarize(neighbor_objectives, weights)

            # Metropolis criterion
            delta_J = neighbor_J - current_J
            if delta_J < 0 or self.rng.rand() < np.exp(-delta_J / max(temperature, 1e-10)):
                current_J = neighbor_J
                current_objectives = neighbor_objectives

                # Add to frontier
                point = ParetoPoint(current_objectives, current_net)
                self.pareto_frontier.add_point(point)
            else:
                # Reject: restore network
                current_net = self._copy_network(self.network)

            temperature *= self.cooling_rate

            self.evaluations += 1

    @staticmethod
    def _copy_network(network: Network) -> Network:
        """Deep copy a network."""
        net = Network(
            num_nodes=network.num_nodes,
            source_id=network.source_id,
            sink_id=network.sink_id,
            fluid=network.fluid,
        )

        for ch in network.channels.values():
            net.add_channel(ch.node_from, ch.node_to, ch.length, ch.radius)

        return net
