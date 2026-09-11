"""NSGA-II: Non-dominated Sorting Genetic Algorithm II."""

from dataclasses import dataclass
from typing import List
import numpy as np
from construtal_flow.network import Network
from construtal_flow.topology import EvolutionaryTopology, TopologyMutator
from construtal_flow.optimization import GradientDescent, ObjectiveType
from .objectives import ObjectiveSet, ParetoPoint
from .pareto import ParetoFrontier


@dataclass
class NSGA2Result:
    """Result from NSGA-II optimization."""

    pareto_frontier: ParetoFrontier
    best_point: ParetoPoint
    generation: int
    evaluations: int
    history_frontier_size: List[int]
    history_hypervolume: List[float]


class NSGA2:
    """Non-dominated Sorting Genetic Algorithm II for multi-objective optimization."""

    def __init__(
        self,
        network: Network,
        population_size: int = 50,
        max_generations: int = 50,
        mutation_rate: float = 0.2,
        seed: int = None,
    ):
        """
        Initialize NSGA-II.

        Args:
            network: Initial network
            population_size: Population size (must be even)
            max_generations: Maximum generations
            mutation_rate: Mutation probability per individual
            seed: Random seed
        """
        self.network = network
        self.population_size = max(population_size // 2 * 2, 2)  # Ensure even
        self.max_generations = max_generations
        self.mutation_rate = mutation_rate
        self.seed = seed

        if seed is not None:
            np.random.seed(seed)

        self.rng = np.random.RandomState(seed)
        self.pareto_frontier = ParetoFrontier()
        self.evaluations = 0

    def optimize(self) -> NSGA2Result:
        """Run NSGA-II optimization."""
        # Initialize population
        population = self._create_initial_population()

        history_frontier_size = []
        history_hypervolume = []

        for gen in range(self.max_generations):
            # Evaluate population
            objectives = [self._evaluate_network(net) for net in population]

            # Non-dominated sorting
            ranks = self._non_dominated_sort(objectives)

            # Crowding distance
            distances = self._crowding_distance(objectives, ranks)

            # Selection & reproduction
            parents = self._select_parents(population, objectives, ranks, distances)

            # Crossover & mutation
            offspring = self._create_offspring(parents)

            # Merge & environmental selection
            combined = population + offspring
            combined_objectives = [self._evaluate_network(net) for net in combined]
            combined_ranks = self._non_dominated_sort(combined_objectives)
            combined_distances = self._crowding_distance(combined_objectives, combined_ranks)

            # Keep best
            population, objectives = self._environmental_selection(
                combined,
                combined_objectives,
                combined_ranks,
                combined_distances,
            )

            # Update frontier
            for net, obj in zip(population, objectives):
                point = ParetoPoint(obj, net, gen)
                self.pareto_frontier.add_point(point)

            # Track history
            history_frontier_size.append(self.pareto_frontier.size())
            history_hypervolume.append(self.pareto_frontier.compute_hypervolume())

        # Get best overall point
        frontier = self.pareto_frontier.get_frontier()
        best_point = frontier[0] if frontier else None

        return NSGA2Result(
            pareto_frontier=self.pareto_frontier,
            best_point=best_point,
            generation=self.max_generations,
            evaluations=self.evaluations,
            history_frontier_size=history_frontier_size,
            history_hypervolume=history_hypervolume,
        )

    def _create_initial_population(self) -> List[Network]:
        """Create initial random population."""
        population = []

        for _ in range(self.population_size):
            # Start with initial network
            net = self._copy_network(self.network)

            # Random mutations
            for _ in range(self.rng.randint(1, 4)):
                mutator = TopologyMutator(net)
                mutation_type = mutator.get_random_mutation(self.rng)
                if mutation_type:
                    mutator.apply_random_mutation(mutation_type, self.rng)

            # Optimize radii
            self._optimize_radii(net)

            population.append(net)

        return population

    def _evaluate_network(self, network: Network) -> np.ndarray:
        """Evaluate all objectives for a network."""
        self.evaluations += 1
        obj_set = ObjectiveSet(network)
        return obj_set.compute_objective_vector()

    def _non_dominated_sort(self, objectives: List[np.ndarray]) -> List[int]:
        """
        Compute rank for each solution (NSGA-II non-dominated sorting).

        Returns:
            Rank array (rank 0 = first front, rank 1 = second front, etc.)
        """
        n = len(objectives)
        ranks = np.zeros(n, dtype=int)

        # Count dominations
        dominates = [[] for _ in range(n)]  # Solutions dominated by i
        dominated_count = [0] * n  # Number of solutions dominating i

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue

                # Check if i dominates j
                if np.all(objectives[i] <= objectives[j]) and np.any(objectives[i] < objectives[j]):
                    dominates[i].append(j)
                elif np.all(objectives[j] <= objectives[i]) and np.any(objectives[j] < objectives[i]):
                    dominated_count[i] += 1

        # Assign ranks iteratively
        current_rank = 0
        ranked = set()

        while len(ranked) < n:
            front = [i for i in range(n) if i not in ranked and dominated_count[i] == 0]

            if not front:
                break

            for i in front:
                ranks[i] = current_rank
                ranked.add(i)

                # Decrease dominated count for solutions dominated by i
                for j in dominates[i]:
                    if j not in ranked:
                        dominated_count[j] -= 1

            current_rank += 1

        return ranks

    def _crowding_distance(self, objectives: List[np.ndarray], ranks: np.ndarray) -> np.ndarray:
        """Compute crowding distance for each solution."""
        n = len(objectives)
        distances = np.zeros(n)

        # For each front
        for rank in np.unique(ranks):
            front = np.where(ranks == rank)[0]

            if len(front) <= 2:
                distances[front] = np.inf  # First two solutions get infinite distance
                continue

            objectives_front = np.array([objectives[i] for i in front])

            # For each objective
            for obj_idx in range(objectives_front.shape[1]):
                obj_values = objectives_front[:, obj_idx]
                sorted_idx = np.argsort(obj_values)

                # Boundary solutions
                distances[front[sorted_idx[0]]] = np.inf
                distances[front[sorted_idx[-1]]] = np.inf

                # Interior solutions
                if len(sorted_idx) > 2:
                    obj_max = obj_values.max()
                    obj_min = obj_values.min()
                    obj_range = obj_max - obj_min

                    if obj_range > 0:
                        for k in range(1, len(sorted_idx) - 1):
                            i = front[sorted_idx[k]]
                            distances[i] += (obj_values[sorted_idx[k + 1]] - obj_values[sorted_idx[k - 1]]) / obj_range

        return distances

    def _select_parents(
        self,
        population: List[Network],
        objectives: List[np.ndarray],
        ranks: np.ndarray,
        distances: np.ndarray,
    ) -> List[Network]:
        """Select parents via tournament selection."""
        parents = []

        for _ in range(len(population)):
            # Tournament of size 2
            i1, i2 = self.rng.choice(len(population), 2, replace=False)

            # Prefer: (1) lower rank, (2) larger distance if same rank
            if ranks[i1] < ranks[i2]:
                parents.append(self._copy_network(population[i1]))
            elif ranks[i1] > ranks[i2]:
                parents.append(self._copy_network(population[i2]))
            elif distances[i1] > distances[i2]:
                parents.append(self._copy_network(population[i1]))
            else:
                parents.append(self._copy_network(population[i2]))

        return parents

    def _create_offspring(self, parents: List[Network]) -> List[Network]:
        """Create offspring via mutation."""
        offspring = []

        for parent in parents:
            child = self._copy_network(parent)

            # Mutation
            if self.rng.rand() < self.mutation_rate:
                mutator = TopologyMutator(child)
                mutation_type = mutator.get_random_mutation(self.rng)
                if mutation_type:
                    mutator.apply_random_mutation(mutation_type, self.rng)

            # Optimize radii
            self._optimize_radii(child)

            offspring.append(child)

        return offspring

    def _environmental_selection(
        self,
        combined: List[Network],
        objectives: List[np.ndarray],
        ranks: np.ndarray,
        distances: np.ndarray,
    ) -> tuple:
        """Select population_size best individuals."""
        # Sort by rank, then by distance
        priorities = np.lexsort((-distances, ranks))

        selected_idx = priorities[:self.population_size]
        selected_pop = [combined[i] for i in selected_idx]
        selected_objs = [objectives[i] for i in selected_idx]

        return selected_pop, selected_objs

    def _optimize_radii(self, network: Network):
        """Optimize channel radii for a network."""
        opt = GradientDescent(
            network,
            max_iterations=10,
            learning_rate=0.01,
            seed=self.seed,
        )
        opt.optimize()

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
