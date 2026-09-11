"""Thermal network: Heat transfer in channel networks."""

import numpy as np
from construtal_flow.network import Network
from construtal_flow.solver import LinearSolver


class ThermalChannel:
    """Represents a thermal resistance element (channel)."""

    def __init__(
        self,
        channel_id: int,
        node_from: int,
        node_to: int,
        length: float,
        radius: float,
        thermal_conductivity: float = 0.6,  # W/(m·K) for water
    ):
        """
        Initialize thermal channel.

        Args:
            channel_id: Unique ID
            node_from: Source node
            node_to: Target node
            length: Channel length (m)
            radius: Channel radius (m)
            thermal_conductivity: Thermal conductivity k (W/(m·K))
        """
        self.id = channel_id
        self.node_from = node_from
        self.node_to = node_to
        self.length = length
        self.radius = radius
        self.k = thermal_conductivity

        # Computed properties
        self.heat_flow = None  # Heat flow Q (W)
        self.delta_T = None  # Temperature drop (K)

    @property
    def area(self) -> float:
        """Cross-sectional area (m²)."""
        return np.pi * self.radius**2

    @property
    def thermal_resistance(self) -> float:
        """
        Thermal resistance (K/W).

        R_thermal = L / (k·A)
        """
        if self.area == 0:
            return float('inf')
        return self.length / (self.k * self.area)

    def compute_temperature_drop(self, Q: float) -> float:
        """
        Compute temperature drop for given heat flow.

        Args:
            Q: Heat flow (W)

        Returns:
            Temperature drop ΔT (K)
        """
        return self.thermal_resistance * Q

    def compute_heat_dissipation(self, Q: float) -> float:
        """
        Compute heat dissipation (irreversible energy).

        Args:
            Q: Heat flow (W)

        Returns:
            Dissipation (W) - same as heat flow in steady-state
        """
        return abs(Q)

    def __repr__(self) -> str:
        return (
            f"ThermalChannel(id={self.id}, {self.node_from}→{self.node_to}, "
            f"L={self.length:.2f}m, r={self.radius:.4f}m, "
            f"R_th={self.thermal_resistance:.2f} K/W)"
        )


class ThermalSolver:
    """Solves thermal network (heat transfer problem)."""

    def __init__(self, network: Network, thermal_conductivity: float = 0.6):
        """
        Initialize thermal solver.

        Args:
            network: Hydraulic network (reuse geometry)
            thermal_conductivity: Material thermal conductivity (W/(m·K))
        """
        self.network = network
        self.k = thermal_conductivity

        # Create thermal channels from hydraulic channels
        self.thermal_channels = {}

        for ch in network.channels.values():
            thermal_ch = ThermalChannel(
                ch.id,
                ch.node_from,
                ch.node_to,
                ch.length,
                ch.radius,
                thermal_conductivity,
            )
            self.thermal_channels[ch.id] = thermal_ch

        # Node temperatures
        self.temperatures = np.zeros(network.num_nodes)

    def solve_temperature_distribution(
        self,
        Q_source: float = 100.0,  # Heat injected at source (W)
        T_sink: float = 0.0,  # Reference temperature at sink (K)
    ) -> bool:
        """
        Solve for temperature distribution in network.

        Uses nodal analysis (same method as hydraulic).

        Args:
            Q_source: Heat input at source (W)
            T_sink: Temperature at sink (K)

        Returns:
            True if converged
        """
        n = self.network.num_nodes

        # Build thermal conductance matrix
        G_thermal = np.zeros((n, n))
        I_thermal = np.zeros(n)

        # For each thermal channel
        for ch in self.thermal_channels.values():
            i = ch.node_from
            j = ch.node_to
            g_th = 1.0 / ch.thermal_resistance  # Thermal conductance

            # Off-diagonal
            G_thermal[i, j] -= g_th
            G_thermal[j, i] -= g_th

            # Diagonal
            G_thermal[i, i] += g_th
            G_thermal[j, j] += g_th

        # Boundary conditions
        I_thermal[self.network.source_id] = Q_source
        I_thermal[self.network.sink_id] = -Q_source

        # Set sink temperature
        G_thermal[self.network.sink_id, :] = 0
        G_thermal[self.network.sink_id, self.network.sink_id] = 1.0
        I_thermal[self.network.sink_id] = T_sink

        # Solve
        try:
            self.temperatures = np.linalg.solve(G_thermal, I_thermal)
        except np.linalg.LinAlgError:
            return False

        # Back-substitute to compute heat flows
        for ch in self.thermal_channels.values():
            i = ch.node_from
            j = ch.node_to

            delta_T = self.temperatures[i] - self.temperatures[j]
            ch.heat_flow = delta_T / ch.thermal_resistance
            ch.delta_T = delta_T

        return True

    def get_thermal_metrics(self) -> dict:
        """
        Compute thermal performance metrics.

        Returns:
            Dictionary with thermal metrics
        """
        if not self.thermal_channels:
            return {}

        # Effective thermal resistance
        T_source = self.temperatures[self.network.source_id]
        T_sink = self.temperatures[self.network.sink_id]
        Q_source = 100.0  # Default

        if Q_source > 0:
            R_eff = (T_source - T_sink) / Q_source
        else:
            R_eff = float('inf')

        # Total dissipation
        Q_diss = sum(
            abs(ch.heat_flow) for ch in self.thermal_channels.values()
            if ch.heat_flow is not None
        )

        # Temperature uniformity
        temps_nonboundary = [
            self.temperatures[i]
            for i in range(self.network.num_nodes)
            if i != self.network.source_id and i != self.network.sink_id
        ]

        if temps_nonboundary:
            temp_std = np.std(temps_nonboundary)
        else:
            temp_std = 0.0

        return {
            "R_eff_thermal": R_eff,
            "Q_dissipation": Q_diss,
            "T_max": np.max(self.temperatures),
            "T_min": np.min(self.temperatures),
            "T_uniformity": temp_std,
        }

    def print_thermal_metrics(self):
        """Print thermal performance metrics."""
        metrics = self.get_thermal_metrics()

        print("Thermal Network Metrics:")
        print(f"  R_eff (thermal): {metrics['R_eff_thermal']:.4f} K/W")
        print(f"  Heat dissipation: {metrics['Q_dissipation']:.2f} W")
        print(f"  T_max: {metrics['T_max']:.2f} K")
        print(f"  T_min: {metrics['T_min']:.2f} K")
        print(f"  Temperature uniformity (std): {metrics['T_uniformity']:.4f} K")
