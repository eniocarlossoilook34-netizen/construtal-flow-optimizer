"""Optimization module: Geometric optimization of channel radii."""

from .objective import ObjectiveFunction, ObjectiveType, compute_objective
from .constraints import ConstraintHandler
from .algorithms import BaseOptimizer, OptimizationResult
from .random_search import RandomSearch
from .gradient_descent import GradientDescent
from .evolutionary import EvolutionaryAlgorithm
from .simulated_annealing import SimulatedAnnealing

__all__ = [
    "ObjectiveFunction",
    "ObjectiveType",
    "compute_objective",
    "ConstraintHandler",
    "BaseOptimizer",
    "OptimizationResult",
    "RandomSearch",
    "GradientDescent",
    "EvolutionaryAlgorithm",
    "SimulatedAnnealing",
]
