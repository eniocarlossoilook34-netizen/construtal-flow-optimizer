"""Random search baseline optimizer."""

import numpy as np
from .algorithms import BaseOptimizer, OptimizationResult


class RandomSearch(BaseOptimizer):
    """Baseline: Pure random search."""

    def optimize(self) -> OptimizationResult:
        """Run random search for max_iterations."""
        self._initialize_optimization()

        for gen in range(self.max_iterations):
            self.generation = gen + 1

            # Generate random feasible configuration
            radii = self.constraints.random_feasible(seed=self.seed + gen if self.seed else None)

            # Evaluate
            J = self._evaluate_and_track(radii)

            # Track history
            self.history_best.append(self.best_objective)
            self.history_mean.append(J)

        return self._finalize_optimization()
