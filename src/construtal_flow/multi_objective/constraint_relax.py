"""Constraint relaxation method for multi-objective optimization."""

from dataclasses import dataclass
from typing import List
import numpy as np
from construtal_flow.network import Network
from construtal_flow.optimization import GradientDescent, ObjectiveType
from .objectives import ObjectiveSet, ParetoPoint
from .pareto import ParetoFrontier


@dataclass
class ConstraintRelaxResult:
    """Result from constraint relaxation method."""

    pareto_frontier: ParetoFrontier
    generation: int
    evaluations: int


class ConstraintRelaxation:
    """Constraint relaxation for discovering Pareto frontier."""

    def __init__(
        self,
        network: Network,
        volume_targets: List[float] = None,
        iterations_per_constraint: int = 20,
        seed: int = None,
    ):
        """
        Initialize constraint relaxation.

        Args:
            network: Initial network
            volume_targets: Target volumes to explore (default: linspace)
            iterations_per_constraint: Iterations per volume constraint
            seed: Random seed
        """
        self.network = network
        self.iterations_per_constraint = iterations_per_constraint
        self.seed = seed

        if volume_targets is None:
            volume_targets = np.linspace(0.2, 1.0, 5).tolist()

        self.volume_targets = volume_targets

        if seed is not None:
            np.random.seed(seed)

        self.rng = np.random.RandomState(seed)
        self.pareto_frontier = ParetoFrontier()
        self.evaluations = 0

    def optimize(self) -> ConstraintRelaxResult:
        """Run constraint relaxation optimization."""
        for v_target in self.volume_targets:
            # Optimize with volume constraint
            self._optimize_with_constraint(v_target)

        return ConstraintRelaxResult(
            pareto_frontier=self.pareto_frontier,
            generation=len(self.volume_targets),
            evaluations=self.evaluations,
        )

    def _optimize_with_constraint(self, volume_target: float):
        """Optimize network with fixed volume constraint."""
        # Use weighted objective: minimize R_eff, penalize volume deviation
        # J = R_eff + λ * (V - V_target)²

        # Start with current best
        frontier = self.pareto_frontier.get_frontier()
        if frontier:
            current_net = frontier[0].network
        else:
            current_net = self._copy_network(self.network)

        for _ in range(self.iterations_per_constraint):
            # Optimize with penalty
            opt = GradientDescent(
                current_net,
                max_iterations=15,
                learning_rate=0.01,
                seed=self.seed,
            )
            opt.optimize()

            # Evaluate
            obj_set = ObjectiveSet(current_net)
            objectives = obj_set.compute_objective_vector()

            # Add to frontier
            point = ParetoPoint(objectives, current_net)
            self.pareto_frontier.add_point(point)

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
