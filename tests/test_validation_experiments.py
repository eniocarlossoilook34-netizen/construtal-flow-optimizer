"""
Validation experiments for Phase 1.

Experiment A: Series channels (analytical reference)
Experiment B: Parallel channels (analytical reference)
Experiment C: Branching network (functional validation)
"""

import pytest
import numpy as np
from construtal_flow.network import Network
from construtal_flow.solver import LinearSolver
from construtal_flow.physics import FluidProperties, Channel


class TestExperimentA:
    """Experiment A: Series channels against Hagen-Poiseuille."""

    def test_series_three_channels(self):
        """Three channels in series."""
        # Create network: 0 (source) -> 1 -> 2 -> 3 (sink)
        net = Network(num_nodes=4, source_id=0, sink_id=3)

        # All identical: L=1m, r=0.05m
        net.add_channel(0, 1, length=1.0, radius=0.05)
        net.add_channel(1, 2, length=1.0, radius=0.05)
        net.add_channel(2, 3, length=1.0, radius=0.05)

        # Solve
        solver = LinearSolver(net)
        pressures, converged = solver.solve()

        assert converged, "Solver did not converge"
        assert solver.validate_solution(), "Solution failed validation"

        # Analytical: R_total = sum of series = 3 * R_single
        ch = net.get_channel(0)
        R_single = ch.resistance
        R_total_analytical = 3 * R_single

        # Computed: R_eff = ΔP / Q_in
        metrics = net.get_network_metrics()
        R_eff_computed = metrics["R_eff"]

        # Compare
        relative_error = abs(R_eff_computed - R_total_analytical) / R_total_analytical
        assert relative_error < 0.01, (
            f"Series resistance mismatch: "
            f"computed={R_eff_computed:.2e}, "
            f"analytical={R_total_analytical:.2e}, "
            f"error={relative_error:.4f}"
        )

    def test_series_different_radii(self):
        """Series channels with different radii."""
        net = Network(num_nodes=3, source_id=0, sink_id=2)

        # Different radii: r1=0.05m, r2=0.03m
        ch1_id = net.add_channel(0, 1, length=1.0, radius=0.05)
        ch2_id = net.add_channel(1, 2, length=1.0, radius=0.03)

        solver = LinearSolver(net)
        pressures, converged = solver.solve()

        assert converged
        assert solver.validate_solution()

        # Analytical
        R1 = net.get_channel(ch1_id).resistance
        R2 = net.get_channel(ch2_id).resistance
        R_total_analytical = R1 + R2

        # Computed
        metrics = net.get_network_metrics()
        R_eff_computed = metrics["R_eff"]

        relative_error = abs(R_eff_computed - R_total_analytical) / R_total_analytical
        assert relative_error < 0.01


class TestExperimentB:
    """Experiment B: Parallel channels."""

    def test_parallel_two_channels(self):
        """Two parallel channels from source to sink."""
        net = Network(num_nodes=2, source_id=0, sink_id=1)

        # Two identical branches: L=1m, r=0.05m each
        net.add_channel(0, 1, length=1.0, radius=0.05)
        net.add_channel(0, 1, length=1.0, radius=0.05)

        solver = LinearSolver(net)
        pressures, converged = solver.solve()

        assert converged
        assert solver.validate_solution()

        # Analytical: R_parallel = R_single / 2
        ch = net.get_channel(0)
        R_single = ch.resistance
        R_total_analytical = R_single / 2.0

        # Computed
        metrics = net.get_network_metrics()
        R_eff_computed = metrics["R_eff"]

        relative_error = abs(R_eff_computed - R_total_analytical) / R_total_analytical
        assert relative_error < 0.01

    def test_parallel_different_radii(self):
        """Parallel channels with different radii."""
        net = Network(num_nodes=2, source_id=0, sink_id=1)

        ch1_id = net.add_channel(0, 1, length=1.0, radius=0.05)
        ch2_id = net.add_channel(0, 1, length=1.0, radius=0.03)

        solver = LinearSolver(net)
        pressures, converged = solver.solve()

        assert converged
        assert solver.validate_solution()

        # Analytical: 1/R_parallel = 1/R1 + 1/R2
        R1 = net.get_channel(ch1_id).resistance
        R2 = net.get_channel(ch2_id).resistance
        R_total_analytical = 1.0 / (1.0 / R1 + 1.0 / R2)

        # Computed
        metrics = net.get_network_metrics()
        R_eff_computed = metrics["R_eff"]

        relative_error = abs(R_eff_computed - R_total_analytical) / R_total_analytical
        assert relative_error < 0.01


class TestExperimentC:
    """Experiment C: Branching network."""

    def test_branching_network(self):
        """
        Network with branching:
        source (0) -> junction (1) -> sink (3)
                   -> branch (2) --|
        """
        net = Network(num_nodes=4, source_id=0, sink_id=3)

        # Main path
        ch1_id = net.add_channel(0, 1, length=1.0, radius=0.05)
        ch3_id = net.add_channel(1, 3, length=1.0, radius=0.05)

        # Branch
        ch2_id = net.add_channel(1, 2, length=1.0, radius=0.04)
        ch4_id = net.add_channel(2, 3, length=1.0, radius=0.04)

        solver = LinearSolver(net)
        pressures, converged = solver.solve()

        assert converged, "Solver did not converge"
        assert solver.validate_solution(), "Solution failed validation"

        # Check that flows are positive (correct direction)
        for ch in net.channels.values():
            assert ch.Q >= 0, f"Channel {ch.id} has negative flow: {ch.Q}"

        # Check flow conservation at junction (node 1)
        ch1 = net.get_channel(ch1_id)
        ch2 = net.get_channel(ch2_id)
        ch3 = net.get_channel(ch3_id)

        Q_in = ch1.Q  # Flow into junction
        Q_out = ch2.Q + ch3.Q  # Flows out of junction

        assert abs(Q_in - Q_out) < 1e-6, (
            f"Flow conservation violated at junction: "
            f"Q_in={Q_in:.2e}, Q_out={Q_out:.2e}"
        )

        # Pressure consistency
        P0, P1, P2, P3 = pressures

        # Check pressure drops
        dP_01 = ch1.compute_pressure_drop(ch1.Q)
        assert abs((P0 - P1) - dP_01) < 1e-3

        ch4 = net.get_channel(ch4_id)
        dP_23 = ch4.compute_pressure_drop(ch4.Q)
        assert abs((P2 - P3) - dP_23) < 1e-3


class TestPhysicsValidation:
    """Test fundamental physics equations."""

    def test_hagen_poiseuille_formula(self):
        """Verify Hagen-Poiseuille resistance calculation."""
        fluid = FluidProperties(viscosity=1e-3, density=1000.0)

        # R = 8μL / (πr⁴)
        mu = fluid.viscosity
        L = 2.0
        r = 0.05

        ch = Channel(0, 0, 1, L, r, fluid)

        # Manual calculation
        R_manual = (8 * mu * L) / (np.pi * r**4)

        assert abs(ch.resistance - R_manual) < 1e-10

    def test_pressure_flow_relation(self):
        """Verify Ohm's law for flow: ΔP = R·Q."""
        ch = Channel(0, 0, 1, length=1.0, radius=0.05)

        Q = 0.5  # m³/s
        dP = ch.compute_pressure_drop(Q)

        expected = ch.resistance * Q
        assert abs(dP - expected) < 1e-10

    def test_velocity_calculation(self):
        """Verify velocity calculation: v = Q/A."""
        ch = Channel(0, 0, 1, length=1.0, radius=0.05)

        Q = 0.1  # m³/s
        v = ch.compute_velocity(Q)

        expected = Q / ch.area
        assert abs(v - expected) < 1e-10

    def test_dissipated_power(self):
        """Verify dissipation: P = ΔP·Q = R·Q²."""
        ch = Channel(0, 0, 1, length=1.0, radius=0.05)

        Q = 0.1
        P_diss = ch.compute_dissipated_power(Q)

        expected = ch.resistance * Q**2
        assert abs(P_diss - expected) < 1e-10


class TestNetworkValidation:
    """Test network-level validation."""

    def test_connectivity_check(self):
        """Test network connectivity validation."""
        net = Network(num_nodes=3, source_id=0, sink_id=2)

        # No channels yet
        assert not net.check_connectivity()

        # Add disconnected channel
        net.add_channel(0, 1, 1.0, 0.05)
        assert not net.check_connectivity()

        # Connect to sink
        net.add_channel(1, 2, 1.0, 0.05)
        assert net.check_connectivity()

    def test_volume_calculation(self):
        """Test total volume calculation."""
        net = Network(num_nodes=2, source_id=0, sink_id=1)

        # Add two identical channels
        net.add_channel(0, 1, length=2.0, radius=0.1)
        net.add_channel(0, 1, length=2.0, radius=0.1)

        # Single channel volume: V = π r² L
        V_single = np.pi * 0.1**2 * 2.0
        V_expected = 2 * V_single

        assert abs(net.total_volume() - V_expected) < 1e-10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
