"""Simulated annealing optimizer."""

import numpy as np
from .algorithms import BaseOptimizer, OptimizationResult


class SimulatedAnnealing(BaseOptimizer):
    """Simulated annealing metaheuristic."""

    def __init__(
        self,
        *args,
        initial_temperature: float = 1.0,
        cooling_rate: float = 0.95,
        perturbation_std: float = 0.01,
        **kwargs,
    ):
        """
        Initialize simulated annealing.

        Args:
            initial_temperature: Initial temperature
            cooling_rate: Temperature scaling factor per iteration
            perturbation_std: Standard deviation of random perturbations
            *args, **kwargs: Passed to BaseOptimizer
        """
        super().__init__(*args, **kwargs)
        self.initial_temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.perturbation_std = perturbation_std

        if self.seed is not None:
            np.random.seed(self.seed)

    def optimize(self) -> OptimizationResult:
        """Run simulated annealing."""
        self._initialize_optimization()

        # Start from initial guess
        current_radii = self._get_initial_guess()
        current_J = self.objective.evaluate(current_radii)

        # Initialize best
        self._evaluate_and_track(current_radii)

        temperature = self.initial_temperature

        for gen in range(self.max_iterations):
            self.generation = gen + 1

            # Propose neighbor solution
            neighbor_radii = np.array(current_radii)

            # Random perturbation
            n_perturb = max(1, int(0.3 * len(neighbor_radii)))
            perturb_idx = np.random.choice(len(neighbor_radii), n_perturb, replace=False)

            for idx in perturb_idx:
                neighbor_radii[idx] += np.random.normal(0, self.perturbation_std * current_radii[idx])

            # Project to feasible
            neighbor_radii = self.constraints.project_to_feasible(neighbor_radii)

            # Evaluate
            neighbor_J = self.objective.evaluate(neighbor_radii)

            # Metropolis criterion
            delta_J = neighbor_J - current_J
            if delta_J < 0 or np.random.rand() < np.exp(-delta_J / max(temperature, 1e-10)):
                # Accept neighbor
                current_radii = neighbor_radii
                current_J = neighbor_J

                # Track if better than best
                self._evaluate_and_track(current_radii)

            # Cool down
            temperature *= self.cooling_rate

            # History
            self.history_best.append(self.best_objective)
            self.history_mean.append(current_J)

        return self._finalize_optimization()
