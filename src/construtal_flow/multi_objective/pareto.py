"""Pareto frontier analysis and dominance checking."""

from typing import List
import numpy as np
from .objectives import ParetoPoint


def is_dominated(point1: np.ndarray, point2: np.ndarray) -> bool:
    """
    Check if point1 is dominated by point2.

    A point is dominated if another point is better in all objectives.
    Since we minimize all objectives, point2 dominates point1 if:
    point2[i] <= point1[i] for all i, and point2[j] < point1[j] for some j

    Args:
        point1: Objective vector to check
        point2: Objective vector to compare against

    Returns:
        True if point1 is dominated by point2
    """
    # Check if point2 is better or equal in all objectives
    all_better_or_equal = np.all(point2 <= point1)

    # Check if point2 is strictly better in at least one
    at_least_one_better = np.any(point2 < point1)

    return all_better_or_equal and at_least_one_better


class ParetoFrontier:
    """Manages and analyzes Pareto frontier."""

    def __init__(self):
        """Initialize empty frontier."""
        self.points: List[ParetoPoint] = []

    def add_point(self, point: ParetoPoint) -> bool:
        """
        Add point to frontier, removing dominated points.

        Args:
            point: ParetoPoint to add

        Returns:
            True if point was added (not dominated), False otherwise
        """
        # Check if new point is dominated by any existing point
        for existing in self.points:
            if is_dominated(point.objectives, existing.objectives):
                return False  # Point is dominated, don't add

        # Remove existing points dominated by new point
        self.points = [
            p for p in self.points
            if not is_dominated(p.objectives, point.objectives)
        ]

        # Add new point
        self.points.append(point)
        return True

    def add_points(self, points: List[ParetoPoint]) -> int:
        """
        Add multiple points to frontier.

        Args:
            points: List of ParetoPoint objects

        Returns:
            Number of points added
        """
        count = 0
        for point in points:
            if self.add_point(point):
                count += 1

        return count

    def get_frontier(self) -> List[ParetoPoint]:
        """Get current Pareto frontier (non-dominated points)."""
        return sorted(self.points, key=lambda p: p.objectives[0])  # Sort by R_eff

    def size(self) -> int:
        """Number of points on frontier."""
        return len(self.points)

    def get_objectives_matrix(self) -> np.ndarray:
        """Get all objectives as matrix (N_points × 4)."""
        return np.array([p.objectives for p in self.points])

    def get_extreme_points(self) -> dict:
        """
        Get extreme points on frontier.

        Returns:
            Dict with best point for each objective
        """
        if not self.points:
            return {}

        objectives_matrix = self.get_objectives_matrix()

        extremes = {}
        objective_names = ["R_eff", "P_diss", "Volume", "Complexity"]

        for i, name in enumerate(objective_names):
            best_idx = np.argmin(objectives_matrix[:, i])
            extremes[name] = self.points[best_idx]

        return extremes

    def compute_hypervolume(self, reference_point: np.ndarray = None) -> float:
        """
        Compute hypervolume (indicator of frontier quality).

        Higher hypervolume = better frontier.

        Args:
            reference_point: Reference point for hypervolume (default: worst case)

        Returns:
            Hypervolume value
        """
        if not self.points:
            return 0.0

        objectives_matrix = self.get_objectives_matrix()

        # Default reference point: 1.5× worst value in each objective
        if reference_point is None:
            reference_point = 1.5 * np.max(objectives_matrix, axis=0)

        # Simple 2D hypervolume (R_eff vs P_diss only)
        # Sort by R_eff
        sorted_idx = np.argsort(objectives_matrix[:, 0])
        sorted_objs = objectives_matrix[sorted_idx]

        hypervolume = 0.0
        prev_pdiss = reference_point[1]

        for i, obj in enumerate(sorted_objs):
            R_eff = obj[0]
            P_diss = obj[1]

            # Rectangle contribution
            width = reference_point[0] - R_eff
            height = prev_pdiss - P_diss

            hypervolume += width * height
            prev_pdiss = P_diss

        return hypervolume

    def print_frontier(self):
        """Print frontier in readable format."""
        print(f"\nPareto Frontier ({self.size()} points):")
        print("-" * 80)
        print(f"{'Rank':<5} {'R_eff':<15} {'P_diss':<15} {'Volume':<12} {'Complexity':<10}")
        print("-" * 80)

        for rank, point in enumerate(self.get_frontier(), 1):
            R_eff, P_diss, Volume, Complexity = point.objectives
            print(f"{rank:<5} {R_eff:<15.4e} {P_diss:<15.4e} {Volume:<12.4f} {Complexity:<10.0f}")

        # Print extremes
        extremes = self.get_extreme_points()
        print("\nExtreme points:")
        for obj_name, point in extremes.items():
            print(f"  Best {obj_name}: {point}")

        # Print hypervolume
        hv = self.compute_hypervolume()
        print(f"\nHypervolume: {hv:.4e}")
