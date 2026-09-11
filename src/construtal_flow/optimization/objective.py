"""Objective functions for network optimization."""

from enum import Enum
from typing import Callable
import numpy as np
from construtal_flow.network import Network
from construtal_flow.solver import LinearSolver


class ObjectiveType(Enum):
    """Types of objective functions."""
    RESISTANCE = "resistance"      # Minimize R_eff
    DISSIPATION = "dissipation"    # Minimize P_diss
    COMBINED = "combined"          # Weighted combination


class ObjectiveFunction:
    """Encapsulates objective function evaluation."""

    def __init__(
        self,
        network: Network,
        obj_type: ObjectiveType = ObjectiveType.RESISTANCE,
        w_R: float = 1.0,
        w_D: float = 0.0,
    ):
        """
        Initialize objective function.

        Args:
            network: Network instance
            obj_type: Type of objective (RESISTANCE, DISSIPATION, COMBINED)
            w_R: Weight for resistance (for COMBINED)
            w_D: Weight for dissipation (for COMBINED)
        """
        self.network = network
        self.obj_type = obj_type
        self.w_R = w_R
        self.w_D = w_D

        # Normalize weights
        w_sum = w_R + w_D
        if w_sum > 0:
            self.w_R /= w_sum
            self.w_D /= w_sum

        self.solver = LinearSolver(network)
        self.evaluation_count = 0

    def evaluate(self, radii: np.ndarray) -> float:
        """
        Evaluate objective function for given radii.

        Args:
            radii: Array of channel radii [r_0, r_1, ..., r_n]

        Returns:
            Objective value (to minimize)
        """
        self.evaluation_count += 1

        # Set radii in network
        for ch_id, r in enumerate(radii):
            if ch_id in self.network.channels:
                self.network.channels[ch_id].radius = r

        # Solve network
        self.network.reset_flows()
        pressures, converged = self.solver.solve()

        if not converged:
            # Return large penalty for non-convergent solutions
            return 1e10

        # Get metrics
        metrics = self.network.get_network_metrics()

        # Compute objective based on type
        if self.obj_type == ObjectiveType.RESISTANCE:
            return metrics["R_eff"]

        elif self.obj_type == ObjectiveType.DISSIPATION:
            return metrics["P_diss_total"]

        elif self.obj_type == ObjectiveType.COMBINED:
            # Normalize both to [0,1] range approximately
            R_eff = metrics["R_eff"]
            P_diss = metrics["P_diss_total"]
            return self.w_R * R_eff + self.w_D * P_diss

        else:
            raise ValueError(f"Unknown objective type: {self.obj_type}")

    def get_baseline(self) -> float:
        """Get baseline (initial) objective value."""
        radii = np.array([ch.radius for ch in self.network.channels.values()])
        return self.evaluate(radii)

    def reset_count(self):
        """Reset evaluation counter."""
        self.evaluation_count = 0


def compute_objective(
    network: Network,
    radii: np.ndarray,
    obj_type: ObjectiveType = ObjectiveType.RESISTANCE,
) -> float:
    """
    Convenience function to evaluate objective without keeping state.

    Args:
        network: Network instance
        radii: Channel radii
        obj_type: Objective type

    Returns:
        Objective value
    """
    obj_fn = ObjectiveFunction(network, obj_type)
    return obj_fn.evaluate(radii)
