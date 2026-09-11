"""Gradient descent optimizer with projection."""

import numpy as np
from .algorithms import BaseOptimizer, OptimizationResult


class GradientDescent(BaseOptimizer):
    """Gradient descent with projection to feasible region."""

    def __init__(self, *args, learning_rate: float = 0.01, **kwargs):
        """
        Initialize gradient descent.

        Args:
            learning_rate: Step size for gradient updates
            *args, **kwargs: Passed to BaseOptimizer
        """
        super().__init__(*args, **kwargs)
        self.learning_rate = learning_rate

    def optimize(self) -> OptimizationResult:
        """Run gradient descent."""
        self._initialize_optimization()

        # Start from initial guess
        radii = self._get_initial_guess()

        for gen in range(self.max_iterations):
            self.generation = gen + 1

            # Compute gradient
            gradient = self.compute_gradient(radii, delta=1e-4)

            # Update step
            radii_new = radii - self.learning_rate * gradient

            # Project to feasible region
            radii_new = self.constraints.project_to_feasible(radii_new)

            # Evaluate
            J_new = self.objective.evaluate(radii_new)

            # Adaptive learning rate: if J got worse, reduce step
            if J_new > self.objective.evaluate(radii):
                self.learning_rate *= 0.8
                radii_new = radii  # Keep old radii
            else:
                self.learning_rate *= 1.05  # Slightly increase if working
                radii = radii_new

            # Track best
            self._evaluate_and_track(radii)

            # History
            self.history_best.append(self.best_objective)
            self.history_mean.append(J_new)

        return self._finalize_optimization()
