"""Evolutionary algorithm (simple genetic algorithm)."""

import numpy as np
from .algorithms import BaseOptimizer, OptimizationResult


class EvolutionaryAlgorithm(BaseOptimizer):
    """Simple genetic algorithm for optimization."""

    def __init__(
        self,
        *args,
        population_size: int = 20,
        mutation_rate: float = 0.1,
        mutation_std: float = 0.01,
        elite_fraction: float = 0.2,
        **kwargs,
    ):
        """
        Initialize evolutionary algorithm.

        Args:
            population_size: Number of individuals
            mutation_rate: Fraction of genes mutated per individual
            mutation_std: Standard deviation of mutations
            elite_fraction: Fraction of best individuals to keep (elite selection)
            *args, **kwargs: Passed to BaseOptimizer
        """
        super().__init__(*args, **kwargs)
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.mutation_std = mutation_std
        self.elite_fraction = max(1, int(elite_fraction * population_size))

        if self.seed is not None:
            np.random.seed(self.seed)

    def optimize(self) -> OptimizationResult:
        """Run genetic algorithm."""
        self._initialize_optimization()

        # Initialize population
        population = [self.constraints.random_feasible() for _ in range(self.population_size)]

        # Evaluate initial population
        fitness = [self.objective.evaluate(ind) for ind in population]

        for gen in range(self.max_iterations):
            self.generation = gen + 1

            # Sort by fitness
            sorted_idx = np.argsort(fitness)
            population = [population[i] for i in sorted_idx]
            fitness = [fitness[i] for i in sorted_idx]

            # Track best
            self._evaluate_and_track(population[0])
            self.history_best.append(self.best_objective)
            self.history_mean.append(np.mean(fitness))

            # Elite selection (keep best individuals)
            new_population = population[: self.elite_fraction].copy()
            new_fitness = fitness[: self.elite_fraction].copy()

            # Generate offspring
            while len(new_population) < self.population_size:
                # Tournament selection: pick best of 2 random
                idx1, idx2 = np.random.randint(0, len(population), 2)
                parent = population[idx1 if fitness[idx1] < fitness[idx2] else idx2]

                # Mutation
                child = np.array(parent)
                n_mutations = max(1, int(self.mutation_rate * len(child)))
                mutation_idx = np.random.choice(len(child), n_mutations, replace=False)

                for idx in mutation_idx:
                    child[idx] += np.random.normal(0, self.mutation_std * parent[idx])

                # Project to feasible
                child = self.constraints.project_to_feasible(child)

                # Crossover with elite (blend with best)
                if np.random.rand() < 0.3:
                    child = 0.7 * child + 0.3 * population[0]
                    child = self.constraints.project_to_feasible(child)

                new_population.append(child)
                new_fitness.append(self.objective.evaluate(child))

            # Truncate to population size
            population = new_population[: self.population_size]
            fitness = new_fitness[: self.population_size]

        return self._finalize_optimization()
