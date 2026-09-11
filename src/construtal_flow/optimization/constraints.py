"""Constraint handling for optimization."""

from typing import Tuple
import numpy as np
from construtal_flow.network import Network
from construtal_flow.physics.constants import Constraints


class ConstraintHandler:
    """Enforces and validates constraints on channel radii."""

    def __init__(self, network: Network, volume_budget: float = 1.0):
        """
        Initialize constraint handler.

        Args:
            network: Network instance
            volume_budget: Total volume available (m³)
        """
        self.network = network
        self.volume_budget = volume_budget

        # Get channel lengths (fixed)
        self.lengths = np.array([ch.length for ch in network.channels.values()])

        # Get number of channels
        self.n_channels = len(network.channels)

    def is_feasible(self, radii: np.ndarray) -> bool:
        """
        Check if radius configuration is feasible.

        Args:
            radii: Array of channel radii

        Returns:
            True if all constraints satisfied
        """
        # Check bounds
        if not np.all(radii >= Constraints.r_min):
            return False
        if not np.all(radii <= Constraints.r_max):
            return False

        # Check volume constraint
        volume = np.sum(np.pi * radii**2 * self.lengths)
        if volume > self.volume_budget:
            return False

        return True

    def project_to_feasible(self, radii: np.ndarray) -> np.ndarray:
        """
        Project radius vector to feasible region.

        Uses simple projection:
        1. Clip to bounds [r_min, r_max]
        2. Scale if volume exceeded

        Args:
            radii: Infeasible radius array

        Returns:
            Feasible radius array
        """
        r = np.array(radii, dtype=float)

        # Clip to bounds
        r = np.clip(r, Constraints.r_min, Constraints.r_max)

        # Check volume
        volume = np.sum(np.pi * r**2 * self.lengths)

        if volume > self.volume_budget:
            # Scale all radii uniformly
            scale = np.sqrt(self.volume_budget / volume)
            r = r * scale
            # Re-clip to bounds
            r = np.clip(r, Constraints.r_min, Constraints.r_max)

        return r

    def random_feasible(self, seed: int = None) -> np.ndarray:
        """
        Generate random feasible radius configuration.

        Args:
            seed: Random seed (for reproducibility)

        Returns:
            Feasible radius array
        """
        if seed is not None:
            np.random.seed(seed)

        # Generate random radii uniformly in [r_min, r_max]
        r = np.random.uniform(Constraints.r_min, Constraints.r_max, self.n_channels)

        # Project to volume constraint
        r = self.project_to_feasible(r)

        return r

    def get_volume(self, radii: np.ndarray) -> float:
        """Get total volume for a radius configuration."""
        return np.sum(np.pi * radii**2 * self.lengths)

    def get_channel_volume(self, radii: np.ndarray, ch_id: int) -> float:
        """Get volume of a single channel."""
        if ch_id >= len(radii):
            return 0.0
        return np.pi * radii[ch_id]**2 * self.lengths[ch_id]

    def volume_remaining(self, radii: np.ndarray) -> float:
        """Get remaining volume budget."""
        return self.volume_budget - self.get_volume(radii)

    def print_info(self, radii: np.ndarray):
        """Print constraint status for a configuration."""
        volume = self.get_volume(radii)
        feasible = self.is_feasible(radii)

        print(f"Configuration info:")
        print(f"  Number of channels: {self.n_channels}")
        print(f"  Volume budget: {self.volume_budget:.6f} m³")
        print(f"  Volume used: {volume:.6f} m³ ({100*volume/self.volume_budget:.1f}%)")
        print(f"  Radius range: {radii.min():.4f} - {radii.max():.4f} m")
        print(f"  Feasible: {'✓ Yes' if feasible else '✗ No'}")

        for i, (r, L) in enumerate(zip(radii, self.lengths)):
            v = self.get_channel_volume(radii, i)
            print(f"    Channel {i}: r={r:.4f}m, L={L:.2f}m, V={v:.6f}m³")
