"""Base optimizer class and utilities."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
from construtal_flow.network import Network
from .objective import ObjectiveFunction, ObjectiveType
from .constraints import ConstraintHandler


@dataclass
class OptimizationResult:
    """Stores optimization results."""

    best_radii: np.ndarray
    best_objective: float
    initial_objective: float
    improvement: float  # (initial - best) / initial
    generations: int
    evaluations: int
    history_best: List[float]
    history_mean: List[float]
    converged: bool

    @property
    def improvement_percent(self) -> float:
        return self.improvement * 100

    def __str__(self) -> str:
        return (
            f"OptimizationResult(\n"
            f"  Best J: {self.best_objective:.4e}\n"
            f"  Initial J: {self.initial_objective:.4e}\n"
            f"  Improvement: {self.improvement_percent:.2f}%\n"
            f"  Generations: {self.generations}\n"
            f"  Evaluations: {self.evaluations}\n"
            f"  Converged: {self.converged}\n"
            f")"
        )


class BaseOptimizer(ABC):
    """Abstract base class for all optimization algorithms."""

    def __init__(
        self,
        network: Network,
        obj_type: ObjectiveType = ObjectiveType.RESISTANCE,
        volume_budget: float = 1.0,
        max_iterations: int = 100,
        seed: int = None,
    ):
        """
        Initialize optimizer.

        Args:
            network: Network to optimize
            obj_type: Objective function type
            volume_budget: Total volume constraint
            max_iterations: Maximum number of iterations
            seed: Random seed for reproducibility
        """
        self.network = network
        self.obj_type = obj_type
        self.volume_budget = volume_budget
        self.max_iterations = max_iterations
        self.seed = seed

        self.objective = ObjectiveFunction(network, obj_type)
        self.constraints = ConstraintHandler(network, volume_budget)

        # Optimization state
        self.best_radii = None
        self.best_objective = float("inf")
        self.initial_objective = None
        self.generation = 0

        # History for convergence plots
        self.history_best = []
        self.history_mean = []

    @abstractmethod
    def optimize(self) -> OptimizationResult:
        """
        Run optimization.

        Must be implemented by subclasses.

        Returns:
            OptimizationResult
        """
        pass

    def _evaluate_and_track(self, radii: np.ndarray) -> float:
        """
        Evaluate objective and update best solution.

        Args:
            radii: Radius configuration

        Returns:
            Objective value
        """
        # Ensure feasibility
        radii = self.constraints.project_to_feasible(radii)

        # Evaluate
        J = self.objective.evaluate(radii)

        # Update best
        if J < self.best_objective:
            self.best_objective = J
            self.best_radii = np.array(radii)

        return J

    def _get_initial_guess(self) -> np.ndarray:
        """Get initial radius configuration."""
        radii = np.array([ch.radius for ch in self.network.channels.values()])
        return radii

    def _initialize_optimization(self):
        """Initialize optimization state."""
        self.objective.reset_count()
        self.generation = 0
        self.history_best = []
        self.history_mean = []

        # Get baseline
        initial_radii = self._get_initial_guess()
        self.initial_objective = self._evaluate_and_track(initial_radii)

    def _finalize_optimization(self) -> OptimizationResult:
        """Finalize and return results."""
        improvement = (self.initial_objective - self.best_objective) / self.initial_objective

        result = OptimizationResult(
            best_radii=self.best_radii,
            best_objective=self.best_objective,
            initial_objective=self.initial_objective,
            improvement=improvement,
            generations=self.generation,
            evaluations=self.objective.evaluation_count,
            history_best=self.history_best,
            history_mean=self.history_mean,
            converged=True,
        )

        return result

    def compute_gradient(self, radii: np.ndarray, delta: float = 1e-4) -> np.ndarray:
        """
        Compute gradient by finite differences.

        Args:
            radii: Current radius configuration
            delta: Perturbation size

        Returns:
            Gradient array (same shape as radii)
        """
        gradient = np.zeros_like(radii, dtype=float)

        for i in range(len(radii)):
            # Forward difference
            radii_plus = np.array(radii)
            radii_plus[i] += delta

            # Evaluate
            J_plus = self._evaluate_and_track(radii_plus)
            J = self.objective.evaluate(radii)

            # Gradient
            gradient[i] = (J_plus - J) / delta

        return gradient
