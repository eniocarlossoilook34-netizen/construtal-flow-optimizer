"""Multi-objective functions for network optimization."""

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
from construtal_flow.network import Network
from construtal_flow.solver import LinearSolver


@dataclass
class ParetoPoint:
    """A point in objective space."""

    objectives: np.ndarray  # [R_eff, P_diss, Volume, Complexity]
    network: Network
    generation: int = 0

    def __iter__(self):
        """Make it iterable over objectives."""
        return iter(self.objectives)

    def __getitem__(self, idx: int) -> float:
        """Access individual objectives."""
        return self.objectives[idx]

    def __repr__(self) -> str:
        return f"ParetoPoint(R={self.objectives[0]:.2e}, P={self.objectives[1]:.2e}, V={self.objectives[2]:.2f}, C={self.objectives[3]:.0f})"


class ObjectiveSet:
    """Evaluates multiple objectives for a network."""

    def __init__(self, network: Network):
        """
        Initialize objective set.

        Args:
            network: Network to evaluate
        """
        self.network = network
        self.solver = LinearSolver(network)

    def compute_all(self) -> Tuple[float, float, float, float]:
        """
        Compute all four objectives.

        Returns:
            (R_eff, P_diss, Volume, Complexity)
        """
        # Solve network
        self.network.reset_flows()
        pressures, converged = self.solver.solve()

        if not converged:
            # Return worst case
            return 1e10, 1e10, 1e10, float(len(self.network.channels))

        # Get metrics
        metrics = self.network.get_network_metrics()

        # Objective 1: Effective resistance (minimize)
        R_eff = metrics["R_eff"]

        # Objective 2: Dissipated power (minimize)
        P_diss = metrics["P_diss_total"]

        # Objective 3: Volume (minimize)
        Volume = self.network.total_volume()

        # Objective 4: Complexity (minimize, but less important)
        # Complexity = number of channels + hierarchy depth
        n_channels = len(self.network.channels)
        Complexity = float(n_channels)

        return R_eff, P_diss, Volume, Complexity

    def compute_objective_vector(self) -> np.ndarray:
        """
        Compute as numpy array [R_eff, P_diss, Volume, Complexity].

        Returns:
            Numpy array of 4 objectives
        """
        objectives = self.compute_all()
        return np.array(objectives)

    def get_pareto_point(self, generation: int = 0) -> ParetoPoint:
        """
        Create a Pareto point from current network state.

        Args:
            generation: Generation number (for tracking)

        Returns:
            ParetoPoint object
        """
        objectives = self.compute_objective_vector()
        return ParetoPoint(objectives, self.network, generation)

    @staticmethod
    def normalize_objectives(objectives: List[np.ndarray]) -> List[np.ndarray]:
        """
        Normalize objectives to [0, 1] range for comparison.

        Args:
            objectives: List of objective vectors

        Returns:
            List of normalized objective vectors
        """
        objectives_array = np.array(objectives)
        n_objs = objectives_array.shape[1]

        normalized = []

        for i in range(n_objs):
            obj_i = objectives_array[:, i]
            min_val = np.min(obj_i)
            max_val = np.max(obj_i)

            if max_val > min_val:
                normalized_i = (obj_i - min_val) / (max_val - min_val)
            else:
                normalized_i = np.zeros_like(obj_i)

            normalized.append(normalized_i)

        return np.array(normalized).T

    @staticmethod
    def scalarize(
        objectives: np.ndarray,
        weights: np.ndarray = None,
    ) -> float:
        """
        Scalarize multiple objectives using weighted sum.

        Args:
            objectives: Array of [R_eff, P_diss, Volume, Complexity]
            weights: Weight vector (default: equal weights)

        Returns:
            Single scalar value to minimize
        """
        if weights is None:
            weights = np.array([0.25, 0.25, 0.25, 0.25])

        # Normalize weights
        weights = weights / np.sum(weights)

        # Weighted sum
        return np.dot(objectives, weights)

    @staticmethod
    def print_objectives(objectives: np.ndarray):
        """Print objectives in readable format."""
        R_eff, P_diss, Volume, Complexity = objectives
        print(f"  R_eff: {R_eff:.4e} Pa·s/m³")
        print(f"  P_diss: {P_diss:.4e} W")
        print(f"  Volume: {Volume:.4f} m³")
        print(f"  Complexity: {Complexity:.0f} channels")
