"""Transport network: Mass diffusion and advection in networks."""

import numpy as np
from construtal_flow.network import Network


class TransportChannel:
    """Represents a transport resistance element (channel)."""

    def __init__(
        self,
        channel_id: int,
        node_from: int,
        node_to: int,
        length: float,
        radius: float,
        diffusion_coefficient: float = 1e-9,  # m²/s for water
    ):
        """
        Initialize transport channel.

        Args:
            channel_id: Unique ID
            node_from: Source node
            node_to: Target node
            length: Channel length (m)
            radius: Channel radius (m)
            diffusion_coefficient: Diffusion coefficient D (m²/s)
        """
        self.id = channel_id
        self.node_from = node_from
        self.node_to = node_to
        self.length = length
        self.radius = radius
        self.D = diffusion_coefficient

        # Computed properties
        self.mass_flow = None  # Mass flow (mol/s or kg/s)
        self.delta_C = None  # Concentration drop

    @property
    def area(self) -> float:
        """Cross-sectional area (m²)."""
        return np.pi * self.radius**2

    @property
    def diffusion_resistance(self) -> float:
        """
        Diffusion resistance (1/(D·A) per unit length).

        R_diffusion = L / (D·A)
        """
        if self.area == 0 or self.D == 0:
            return float('inf')
        return self.length / (self.D * self.area)

    def compute_concentration_drop(self, J: float) -> float:
        """
        Compute concentration drop for given mass flux.

        Args:
            J: Mass flux (mol/s)

        Returns:
            Concentration drop ΔC (mol/m³ or similar)
        """
        return self.diffusion_resistance * J

    def compute_delivery_time(self) -> float:
        """
        Compute characteristic diffusion time.

        t_diff = L² / D (characteristic time scale)
        """
        if self.D == 0:
            return float('inf')
        return self.length**2 / self.D

    def __repr__(self) -> str:
        return (
            f"TransportChannel(id={self.id}, {self.node_from}→{self.node_to}, "
            f"L={self.length:.2f}m, r={self.radius:.4f}m, "
            f"R_diff={self.diffusion_resistance:.2e} (1/(D·A)·m))"
        )


class TransportSolver:
    """Solves transport network (diffusion problem)."""

    def __init__(self, network: Network, diffusion_coefficient: float = 1e-9):
        """
        Initialize transport solver.

        Args:
            network: Hydraulic network (reuse geometry)
            diffusion_coefficient: Mass diffusion coefficient (m²/s)
        """
        self.network = network
        self.D = diffusion_coefficient

        # Create transport channels from hydraulic channels
        self.transport_channels = {}

        for ch in network.channels.values():
            transport_ch = TransportChannel(
                ch.id,
                ch.node_from,
                ch.node_to,
                ch.length,
                ch.radius,
                diffusion_coefficient,
            )
            self.transport_channels[ch.id] = transport_ch

        # Node concentrations
        self.concentrations = np.zeros(network.num_nodes)

    def solve_concentration_distribution(
        self,
        J_source: float = 1.0,  # Mass source (mol/s)
        C_sink: float = 0.0,  # Reference concentration at sink
    ) -> bool:
        """
        Solve for concentration distribution via diffusion.

        Uses nodal analysis (same as hydraulic/thermal).

        Args:
            J_source: Mass injection at source (mol/s)
            C_sink: Concentration at sink

        Returns:
            True if converged
        """
        n = self.network.num_nodes

        # Build diffusion conductance matrix
        G_diff = np.zeros((n, n))
        I_diff = np.zeros(n)

        # For each transport channel
        for ch in self.transport_channels.values():
            i = ch.node_from
            j = ch.node_to
            g_diff = 1.0 / ch.diffusion_resistance  # Diffusion conductance

            # Off-diagonal
            G_diff[i, j] -= g_diff
            G_diff[j, i] -= g_diff

            # Diagonal
            G_diff[i, i] += g_diff
            G_diff[j, j] += g_diff

        # Boundary conditions
        I_diff[self.network.source_id] = J_source
        I_diff[self.network.sink_id] = -J_source

        # Set sink concentration
        G_diff[self.network.sink_id, :] = 0
        G_diff[self.network.sink_id, self.network.sink_id] = 1.0
        I_diff[self.network.sink_id] = C_sink

        # Solve
        try:
            self.concentrations = np.linalg.solve(G_diff, I_diff)
        except np.linalg.LinAlgError:
            return False

        # Back-substitute to compute mass flows
        for ch in self.transport_channels.values():
            i = ch.node_from
            j = ch.node_to

            delta_C = self.concentrations[i] - self.concentrations[j]
            ch.mass_flow = delta_C / ch.diffusion_resistance
            ch.delta_C = delta_C

        return True

    def get_transport_metrics(self) -> dict:
        """
        Compute transport performance metrics.

        Returns:
            Dictionary with transport metrics
        """
        if not self.transport_channels:
            return {}

        # Effective diffusion resistance
        C_source = self.concentrations[self.network.source_id]
        C_sink = self.concentrations[self.network.sink_id]
        J_source = 1.0  # Default

        if J_source > 0:
            R_eff = (C_source - C_sink) / J_source
        else:
            R_eff = float('inf')

        # Total delivery efficiency
        J_delivered = sum(
            abs(ch.mass_flow) for ch in self.transport_channels.values()
            if ch.mass_flow is not None
        )

        # Delivery time (based on diffusion timescale)
        delivery_times = [
            ch.compute_delivery_time()
            for ch in self.transport_channels.values()
        ]
        max_delivery_time = max(delivery_times) if delivery_times else 0

        # Concentration uniformity
        conc_nonboundary = [
            self.concentrations[i]
            for i in range(self.network.num_nodes)
            if i != self.network.source_id and i != self.network.sink_id
        ]

        if conc_nonboundary:
            conc_std = np.std(conc_nonboundary)
        else:
            conc_std = 0.0

        return {
            "R_eff_diffusion": R_eff,
            "J_delivered": J_delivered,
            "C_max": np.max(self.concentrations),
            "C_min": np.min(self.concentrations),
            "C_uniformity": conc_std,
            "max_delivery_time": max_delivery_time,
        }

    def print_transport_metrics(self):
        """Print transport performance metrics."""
        metrics = self.get_transport_metrics()

        print("Transport Network Metrics:")
        print(f"  R_eff (diffusion): {metrics['R_eff_diffusion']:.4e} (1/(D·A)·m)")
        print(f"  Mass delivered: {metrics['J_delivered']:.2f} mol/s")
        print(f"  C_max: {metrics['C_max']:.4e} mol/m³")
        print(f"  C_min: {metrics['C_min']:.4e} mol/m³")
        print(f"  Concentration uniformity (std): {metrics['C_uniformity']:.4e}")
        print(f"  Max delivery time: {metrics['max_delivery_time']:.2e} s")
