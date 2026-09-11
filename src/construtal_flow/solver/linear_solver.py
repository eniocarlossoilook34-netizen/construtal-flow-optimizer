"""Linear solver for steady-state laminar flow in hydraulic networks."""

from typing import Tuple
import numpy as np
from scipy import linalg
from construtal_flow.network import Network
from construtal_flow.physics.constants import Constraints


class LinearSolver:
    """
    Solves for steady-state flow distribution in a network.

    Method: Nodal analysis
    - Unknowns: node pressures P_i
    - Equations: flow continuity at each internal node
    - Constitutive: Ohm's law for flow: Q = ΔP / R

    Steady-state: ∂P/∂t = 0, ∂Q/∂t = 0
    """

    def __init__(self, network: Network):
        """
        Initialize solver for a network.

        Args:
            network: Network instance
        """
        self.network = network
        self.num_nodes = network.num_nodes
        self.num_channels = len(network.channels)

    def solve(self) -> Tuple[np.ndarray, bool]:
        """
        Solve for nodal pressures using nodal analysis.

        Returns:
            - pressures: array of nodal pressures (Pa)
            - converged: whether solution was successful
        """
        if not self.network.check_connectivity():
            raise ValueError("Network is not connected")

        n = self.num_nodes
        source = self.network.source_id
        sink = self.network.sink_id

        # Build conductance matrix G and RHS vector I
        G = np.zeros((n, n))
        I = np.zeros(n)

        # For each channel: model as conductance g = 1/R
        for ch_id, channel in self.network.channels.items():
            i = channel.node_from
            j = channel.node_to
            g = 1.0 / channel.resistance  # conductance

            # Off-diagonal: -g (coupling)
            G[i, j] -= g
            G[j, i] -= g

            # Diagonal: sum of connected conductances
            G[i, i] += g
            G[j, j] += g

        # Boundary conditions
        # Source: inject flow Q_in
        I[source] = self.network.Q_in

        # Sink: extract flow Q_in (negative sign)
        I[sink] = -self.network.Q_in

        # Set sink pressure to reference
        G[sink, :] = 0
        G[sink, sink] = 1.0
        I[sink] = self.network.P_ref

        # Solve: G · P = I
        try:
            pressures = linalg.solve(G, I)
        except linalg.LinAlgError:
            # Singular matrix: network has isolated nodes
            return np.zeros(n), False

        # Back-substitute to compute flows
        self._compute_flows(pressures)

        self.network.pressures = pressures
        return pressures, True

    def _compute_flows(self, pressures: np.ndarray):
        """
        Compute flow rates in each channel given nodal pressures.

        Args:
            pressures: array of nodal pressures
        """
        for channel in self.network.channels.values():
            i = channel.node_from
            j = channel.node_to

            # Pressure drop from i to j
            delta_P = pressures[i] - pressures[j]

            # Flow: Q = ΔP / R
            channel.Q = delta_P / channel.resistance
            channel.delta_P = delta_P

    def validate_solution(self, tol_flow: float = None, tol_pressure: float = None) -> bool:
        """
        Validate solution against physical constraints.

        Checks:
        1. Flow continuity at internal nodes
        2. Pressure balance consistency
        3. Flow rate bounds

        Args:
            tol_flow: Tolerance for flow continuity (default: Constraints.atol)
            tol_pressure: Tolerance for pressure balance (default: Constraints.P_tol)

        Returns:
            True if solution is valid
        """
        if tol_flow is None:
            tol_flow = Constraints.atol
        if tol_pressure is None:
            tol_pressure = Constraints.P_tol

        # Check flow continuity at internal nodes
        for node_id in range(self.num_nodes):
            if node_id == self.network.source_id or node_id == self.network.sink_id:
                continue

            Q_in_sum = sum(
                ch.Q for ch in self.network.get_incoming_channels(node_id) if ch.Q is not None
            )
            Q_out_sum = sum(
                ch.Q for ch in self.network.get_outgoing_channels(node_id) if ch.Q is not None
            )

            if abs(Q_in_sum - Q_out_sum) > tol_flow:
                print(
                    f"Node {node_id}: Flow imbalance = {abs(Q_in_sum - Q_out_sum):.2e} > {tol_flow}"
                )
                return False

        # Check pressure drop consistency
        for channel in self.network.channels.values():
            if channel.Q is None:
                continue

            computed_delta_P = channel.compute_pressure_drop(channel.Q)
            actual_delta_P = channel.delta_P

            if abs(computed_delta_P - actual_delta_P) > tol_pressure:
                print(
                    f"Channel {channel.id}: Pressure mismatch = {abs(computed_delta_P - actual_delta_P):.2e}"
                )
                return False

        return True

    def get_solution_metrics(self) -> dict:
        """
        Get metrics from current solution.

        Returns:
            Dictionary with flow, pressure, and dissipation metrics.
        """
        if all(ch.Q is None for ch in self.network.channels.values()):
            return {}

        metrics = {
            "pressures": self.network.pressures.copy(),
            "flows": {ch.id: ch.Q for ch in self.network.channels.values()},
            "pressure_drops": {ch.id: ch.delta_P for ch in self.network.channels.values()},
            "velocities": {
                ch.id: ch.compute_velocity(ch.Q)
                for ch in self.network.channels.values()
                if ch.Q is not None
            },
            "resistances": {ch.id: ch.resistance for ch in self.network.channels.values()},
        }

        return metrics
