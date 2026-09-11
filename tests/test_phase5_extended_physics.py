"""Tests for Phase 5: Extended physics (thermal, transport)."""

import pytest
import numpy as np
from construtal_flow.network import Network
from construtal_flow.physics_extended.thermal_network import ThermalChannel, ThermalSolver
from construtal_flow.physics_extended.transport_network import (
    TransportChannel,
    TransportSolver,
)
from construtal_flow.physics_extended.material_properties import (
    WATER,
    GLYCERIN,
    AIR,
    MaterialProperties,
)


class TestThermalChannel:
    """Test thermal channel physics."""

    def test_thermal_channel_creation(self):
        """Test thermal channel initialization."""
        ch = ThermalChannel(0, 0, 1, length=1.0, radius=0.01, thermal_conductivity=0.6)
        assert ch.id == 0
        assert ch.node_from == 0
        assert ch.node_to == 1
        assert ch.length == 1.0
        assert ch.k == 0.6

    def test_thermal_resistance(self):
        """Test thermal resistance calculation: R_th = L / (k*A)."""
        ch = ThermalChannel(0, 0, 1, length=1.0, radius=0.01, thermal_conductivity=0.6)

        # R_th = L / (k * π*r²)
        A = np.pi * 0.01**2
        expected_R = 1.0 / (0.6 * A)

        assert np.isclose(ch.thermal_resistance, expected_R)

    def test_temperature_drop(self):
        """Test temperature drop calculation: ΔT = R_th * Q."""
        ch = ThermalChannel(0, 0, 1, length=1.0, radius=0.01, thermal_conductivity=0.6)
        Q = 100.0  # 100 W

        delta_T = ch.compute_temperature_drop(Q)
        expected = ch.thermal_resistance * Q

        assert np.isclose(delta_T, expected)

    def test_heat_dissipation(self):
        """Test heat dissipation (equals heat flow in steady-state)."""
        ch = ThermalChannel(0, 0, 1, length=1.0, radius=0.01, thermal_conductivity=0.6)
        Q = 50.0

        diss = ch.compute_heat_dissipation(Q)
        assert np.isclose(diss, abs(Q))

    def test_thermal_channel_area(self):
        """Test cross-sectional area calculation."""
        ch = ThermalChannel(0, 0, 1, length=1.0, radius=0.02, thermal_conductivity=0.6)
        expected_A = np.pi * 0.02**2
        assert np.isclose(ch.area, expected_A)


class TestTransportChannel:
    """Test transport channel physics."""

    def test_transport_channel_creation(self):
        """Test transport channel initialization."""
        ch = TransportChannel(
            0, 0, 1, length=1.0, radius=0.01, diffusion_coefficient=1e-9
        )
        assert ch.id == 0
        assert ch.length == 1.0
        assert ch.D == 1e-9

    def test_diffusion_resistance(self):
        """Test diffusion resistance: R_diff = L / (D*A)."""
        ch = TransportChannel(
            0, 0, 1, length=1.0, radius=0.01, diffusion_coefficient=1e-9
        )

        A = np.pi * 0.01**2
        expected_R = 1.0 / (1e-9 * A)

        assert np.isclose(ch.diffusion_resistance, expected_R)

    def test_concentration_drop(self):
        """Test concentration drop: ΔC = R_diff * J."""
        ch = TransportChannel(
            0, 0, 1, length=1.0, radius=0.01, diffusion_coefficient=1e-9
        )
        J = 1.0

        delta_C = ch.compute_concentration_drop(J)
        expected = ch.diffusion_resistance * J

        assert np.isclose(delta_C, expected)

    def test_delivery_time(self):
        """Test diffusion timescale: t = L² / D."""
        ch = TransportChannel(
            0, 0, 1, length=1.0, radius=0.01, diffusion_coefficient=1e-9
        )

        t = ch.compute_delivery_time()
        expected = 1.0**2 / 1e-9

        assert np.isclose(t, expected)


class TestThermalSolver:
    """Test thermal network solver."""

    def test_thermal_solver_creation(self):
        """Test thermal solver initialization."""
        net = Network(num_nodes=3, source_id=0, sink_id=2)
        net.add_channel(0, 1, 1.0, 0.01)
        net.add_channel(1, 2, 1.0, 0.01)

        solver = ThermalSolver(net, thermal_conductivity=0.6)

        assert solver.network == net
        assert len(solver.thermal_channels) == 2

    def test_thermal_solver_series_network(self):
        """Test thermal solver on series network."""
        net = Network(num_nodes=3, source_id=0, sink_id=2)
        net.add_channel(0, 1, 1.0, 0.01)
        net.add_channel(1, 2, 1.0, 0.01)

        solver = ThermalSolver(net, thermal_conductivity=0.6)
        success = solver.solve_temperature_distribution(Q_source=100.0, T_sink=300.0)

        assert success
        # Source should have higher temperature
        assert solver.temperatures[0] > solver.temperatures[2]

    def test_thermal_metrics(self):
        """Test thermal metrics computation."""
        net = Network(num_nodes=3, source_id=0, sink_id=2)
        net.add_channel(0, 1, 1.0, 0.01)
        net.add_channel(1, 2, 1.0, 0.01)

        solver = ThermalSolver(net, thermal_conductivity=0.6)
        solver.solve_temperature_distribution(Q_source=100.0, T_sink=300.0)

        metrics = solver.get_thermal_metrics()

        assert "R_eff_thermal" in metrics
        assert "Q_dissipation" in metrics
        assert "T_max" in metrics
        assert "T_min" in metrics
        assert "T_uniformity" in metrics

    def test_thermal_solver_convergence(self):
        """Test that solver produces valid results."""
        net = Network(num_nodes=4, source_id=0, sink_id=3)
        net.add_channel(0, 1, 1.0, 0.01)
        net.add_channel(1, 2, 0.5, 0.01)
        net.add_channel(1, 3, 0.5, 0.01)

        solver = ThermalSolver(net, thermal_conductivity=0.6)
        success = solver.solve_temperature_distribution(Q_source=100.0, T_sink=300.0)

        assert success
        assert len(solver.temperatures) == 4
        assert np.all(np.isfinite(solver.temperatures))


class TestTransportSolver:
    """Test transport network solver."""

    def test_transport_solver_creation(self):
        """Test transport solver initialization."""
        net = Network(num_nodes=3, source_id=0, sink_id=2)
        net.add_channel(0, 1, 1.0, 0.01)
        net.add_channel(1, 2, 1.0, 0.01)

        solver = TransportSolver(net, diffusion_coefficient=1e-9)

        assert solver.network == net
        assert len(solver.transport_channels) == 2

    def test_transport_solver_series_network(self):
        """Test transport solver on series network."""
        net = Network(num_nodes=3, source_id=0, sink_id=2)
        net.add_channel(0, 1, 1.0, 0.01)
        net.add_channel(1, 2, 1.0, 0.01)

        solver = TransportSolver(net, diffusion_coefficient=1e-9)
        success = solver.solve_concentration_distribution(J_source=1.0, C_sink=0.0)

        assert success
        # Source should have higher concentration
        assert solver.concentrations[0] > solver.concentrations[2]

    def test_transport_metrics(self):
        """Test transport metrics computation."""
        net = Network(num_nodes=3, source_id=0, sink_id=2)
        net.add_channel(0, 1, 1.0, 0.01)
        net.add_channel(1, 2, 1.0, 0.01)

        solver = TransportSolver(net, diffusion_coefficient=1e-9)
        solver.solve_concentration_distribution(J_source=1.0, C_sink=0.0)

        metrics = solver.get_transport_metrics()

        assert "R_eff_diffusion" in metrics
        assert "J_delivered" in metrics
        assert "C_max" in metrics
        assert "C_min" in metrics
        assert "C_uniformity" in metrics

    def test_transport_solver_convergence(self):
        """Test that solver produces valid results."""
        net = Network(num_nodes=4, source_id=0, sink_id=3)
        net.add_channel(0, 1, 1.0, 0.01)
        net.add_channel(1, 2, 0.5, 0.01)
        net.add_channel(1, 3, 0.5, 0.01)

        solver = TransportSolver(net, diffusion_coefficient=1e-9)
        success = solver.solve_concentration_distribution(J_source=1.0, C_sink=0.0)

        assert success
        assert len(solver.concentrations) == 4
        assert np.all(np.isfinite(solver.concentrations))


class TestMaterialProperties:
    """Test material property models."""

    def test_material_creation(self):
        """Test material property initialization."""
        mat = MaterialProperties(
            name="Test Fluid",
            viscosity_ref=0.001,
            thermal_conductivity_ref=0.5,
        )

        assert mat.name == "Test Fluid"
        assert mat.viscosity_ref == 0.001
        assert mat.thermal_conductivity_ref == 0.5

    def test_water_properties(self):
        """Test water material properties."""
        assert WATER.name == "Water"
        assert WATER.viscosity_ref == 1e-3
        assert WATER.thermal_conductivity_ref == 0.6

    def test_viscosity_temperature_dependence(self):
        """Test temperature-dependent viscosity."""
        T_ref = 293.15
        T_hot = 313.15  # 20°C hotter

        mu_ref = WATER.viscosity(T_ref)
        mu_hot = WATER.viscosity(T_hot)

        # Viscosity should decrease with temperature (negative alpha coefficient)
        assert mu_hot < mu_ref

    def test_thermal_conductivity_temperature_dependence(self):
        """Test temperature-dependent thermal conductivity."""
        T_ref = 293.15
        T_hot = 313.15

        k_ref = WATER.thermal_conductivity(T_ref)
        k_hot = WATER.thermal_conductivity(T_hot)

        # For water, k increases slightly with temperature
        assert k_hot > k_ref

    def test_diffusion_coefficient_temperature_dependence(self):
        """Test temperature-dependent diffusion coefficient."""
        T_ref = 293.15
        T_hot = 313.15

        D_ref = WATER.diffusion_coefficient(T_ref)
        D_hot = WATER.diffusion_coefficient(T_hot)

        # Diffusion increases with temperature
        assert D_hot > D_ref

    def test_density_temperature_dependence(self):
        """Test temperature-dependent density."""
        T_ref = 293.15
        T_hot = 313.15

        rho_ref = WATER.density(T_ref)
        rho_hot = WATER.density(T_hot)

        # Density decreases with temperature (thermal expansion)
        assert rho_hot < rho_ref

    def test_material_comparison(self):
        """Test comparison of different materials at same conditions."""
        T = 293.15

        mu_water = WATER.viscosity(T)
        mu_air = AIR.viscosity(T)

        # Water is more viscous than air
        assert mu_water > mu_air

        k_glycerin = GLYCERIN.thermal_conductivity(T)
        k_water = WATER.thermal_conductivity(T)

        # Water has better thermal conductivity than glycerin
        assert k_water > k_glycerin


class TestCoupledPhysics:
    """Test coupled multi-physics scenarios."""

    def test_thermal_affects_transport(self):
        """Test that temperature affects diffusion in transport."""
        net = Network(num_nodes=3, source_id=0, sink_id=2)
        net.add_channel(0, 1, 1.0, 0.01)
        net.add_channel(1, 2, 1.0, 0.01)

        # Solve at two different temperatures
        T_cold = 283.15
        T_hot = 313.15

        D_cold = WATER.diffusion_coefficient(T_cold)
        D_hot = WATER.diffusion_coefficient(T_hot)

        solver_cold = TransportSolver(net, diffusion_coefficient=D_cold)
        solver_hot = TransportSolver(net, diffusion_coefficient=D_hot)

        solver_cold.solve_concentration_distribution(J_source=1.0, C_sink=0.0)
        solver_hot.solve_concentration_distribution(J_source=1.0, C_sink=0.0)

        metrics_cold = solver_cold.get_transport_metrics()
        metrics_hot = solver_hot.get_transport_metrics()

        # Higher temperature -> lower resistance -> faster transport
        assert metrics_hot["R_eff_diffusion"] < metrics_cold["R_eff_diffusion"]

    def test_parallel_network_thermal(self):
        """Test thermal solver on parallel network."""
        net = Network(num_nodes=4, source_id=0, sink_id=3)
        # Parallel branches: 0 -> 1 -> 3
        #                   0 -> 2 -> 3
        net.add_channel(0, 1, 1.0, 0.01)
        net.add_channel(0, 2, 1.0, 0.01)
        net.add_channel(1, 3, 1.0, 0.01)
        net.add_channel(2, 3, 1.0, 0.01)

        solver = ThermalSolver(net, thermal_conductivity=0.6)
        success = solver.solve_temperature_distribution(Q_source=100.0, T_sink=300.0)

        assert success
        # Parallel path should distribute temperature more evenly
        T_intermediate = [solver.temperatures[1], solver.temperatures[2]]
        assert np.std(T_intermediate) < 20  # Within 20K of each other


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
