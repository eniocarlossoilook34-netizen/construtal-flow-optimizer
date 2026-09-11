"""Channel physics: Hagen-Poiseuille flow in cylindrical channels."""

import numpy as np
from .constants import FluidProperties, Constraints


class Channel:
    """
    Represents a cylindrical channel in a hydraulic network.

    Implements laminar, incompressible, steady-state Hagen-Poiseuille flow.
    """

    def __init__(
        self,
        channel_id: int,
        node_from: int,
        node_to: int,
        length: float,
        radius: float,
        fluid: FluidProperties = None,
    ):
        """
        Initialize a channel.

        Args:
            channel_id: Unique channel identifier
            node_from: Source node index
            node_to: Target node index
            length: Channel length (m)
            radius: Channel radius (m)
            fluid: FluidProperties instance (default: water-like)
        """
        self.id = channel_id
        self.node_from = node_from
        self.node_to = node_to
        self.length = length
        self.radius = radius
        self.fluid = fluid or FluidProperties()

        # Validate geometry
        if not (Constraints.L_min <= length <= Constraints.L_max):
            raise ValueError(
                f"Channel length {length} outside bounds "
                f"[{Constraints.L_min}, {Constraints.L_max}]"
            )
        if not (Constraints.r_min <= radius <= Constraints.r_max):
            raise ValueError(
                f"Channel radius {radius} outside bounds "
                f"[{Constraints.r_min}, {Constraints.r_max}]"
            )

        # Computed properties
        self.Q = None  # Volumetric flow rate (m³/s)
        self.delta_P = None  # Pressure drop (Pa)

    @property
    def area(self) -> float:
        """Cross-sectional area (m²)."""
        return np.pi * self.radius**2

    @property
    def volume(self) -> float:
        """Channel volume (m³)."""
        return self.area * self.length

    @property
    def resistance(self) -> float:
        """
        Hydraulic resistance (Pa·s/m³).

        From Hagen-Poiseuille: R_h = 8μL/(πr⁴)
        """
        return (8 * self.fluid.viscosity * self.length) / (
            np.pi * self.radius**4
        )

    def compute_pressure_drop(self, Q: float) -> float:
        """
        Compute pressure drop for given volumetric flow rate.

        Args:
            Q: Volumetric flow rate (m³/s)

        Returns:
            Pressure drop ΔP = R_h · Q (Pa)
        """
        return self.resistance * Q

    def compute_velocity(self, Q: float) -> float:
        """
        Compute mean flow velocity.

        Args:
            Q: Volumetric flow rate (m³/s)

        Returns:
            Mean velocity v = Q/A (m/s)
        """
        if self.area == 0:
            return 0.0
        return Q / self.area

    def compute_dissipated_power(self, Q: float) -> float:
        """
        Compute viscous dissipation power.

        Args:
            Q: Volumetric flow rate (m³/s)

        Returns:
            Dissipated power P_diss = ΔP · Q (W)
        """
        return self.resistance * Q**2

    def check_constraints(self) -> bool:
        """Check if channel satisfies all constraints."""
        # Geometry bounds
        if not (Constraints.L_min <= self.length <= Constraints.L_max):
            return False
        if not (Constraints.r_min <= self.radius <= Constraints.r_max):
            return False
        return True

    def __repr__(self) -> str:
        return (
            f"Channel(id={self.id}, {self.node_from}→{self.node_to}, "
            f"L={self.length:.3f}m, r={self.radius:.4f}m, "
            f"R={self.resistance:.2e} Pa·s/m³)"
        )
