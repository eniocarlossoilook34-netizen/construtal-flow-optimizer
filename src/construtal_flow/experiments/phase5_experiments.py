"""Phase 5 experiments: Extended physics (thermal, transport, multi-physics)."""

import numpy as np
import matplotlib.pyplot as plt
from construtal_flow.network import Network
from construtal_flow.physics_extended.thermal_network import ThermalSolver
from construtal_flow.physics_extended.transport_network import TransportSolver
from construtal_flow.physics_extended.material_properties import (
    WATER,
    GLYCERIN,
    AIR,
    SILICON_OIL,
)


def create_test_network_phase5() -> Network:
    """Create a simple branching network for Phase 5 experiments."""
    net = Network(num_nodes=5, source_id=0, sink_id=4)

    # Simple tree: 0 -> 1 -> 2 -> 4
    #                   -> 3 -> 4
    net.add_channel(0, 1, 1.0, 0.01)
    net.add_channel(1, 2, 0.5, 0.01)
    net.add_channel(1, 3, 0.5, 0.01)
    net.add_channel(2, 4, 0.5, 0.01)
    net.add_channel(3, 4, 0.5, 0.01)

    return net


def experiment1_thermal_basic():
    """Experiment 1: Basic thermal network analysis."""
    print("\n" + "=" * 60)
    print("EXPERIMENT 1: Basic Thermal Network")
    print("=" * 60)

    net = create_test_network_phase5()

    # Create thermal solver with different materials
    for material in [WATER, GLYCERIN, SILICON_OIL]:
        print(f"\n--- {material.name} ---")
        solver = ThermalSolver(net, thermal_conductivity=material.thermal_conductivity_ref)

        # Solve with reference temperature
        Q_in = 100.0  # 100 W heat input
        T_ref = 300.0  # Reference at sink

        success = solver.solve_temperature_distribution(Q_source=Q_in, T_sink=T_ref)

        if success:
            solver.print_thermal_metrics()
            print(f"  Temperature distribution: {solver.temperatures}")
        else:
            print("  Solver failed to converge")


def experiment2_thermal_temperature_dependent():
    """Experiment 2: Temperature-dependent thermal properties."""
    print("\n" + "=" * 60)
    print("EXPERIMENT 2: Temperature-Dependent Thermal Properties")
    print("=" * 60)

    net = create_test_network_phase5()

    print("\nComparing water thermal properties at different temperatures:")
    temperatures = [283.15, 293.15, 303.15, 313.15]  # 10°C, 20°C, 30°C, 40°C

    for T in temperatures:
        k = WATER.thermal_conductivity(T)
        print(f"  T = {T-273.15:.0f}°C: k = {k:.4f} W/(m·K)")

    # Simulate heat transfer with varying thermal conductivity
    print("\nThermal network at different ambient temperatures:")

    for T_ambient in [280.0, 300.0, 320.0]:
        solver = ThermalSolver(
            net, thermal_conductivity=WATER.thermal_conductivity(T_ambient)
        )
        success = solver.solve_temperature_distribution(Q_source=100.0, T_sink=T_ambient)

        if success:
            metrics = solver.get_thermal_metrics()
            print(f"\n  Ambient T = {T_ambient-273.15:.0f}°C")
            print(f"    R_eff = {metrics['R_eff_thermal']:.4f} K/W")
            print(f"    T_max = {metrics['T_max']:.1f} K")


def experiment3_transport_basic():
    """Experiment 3: Basic diffusion/transport network."""
    print("\n" + "=" * 60)
    print("EXPERIMENT 3: Basic Transport Network (Diffusion)")
    print("=" * 60)

    net = create_test_network_phase5()

    # Test with different diffusion coefficients
    diffusion_coeff = [1e-10, 1e-9, 1e-8]

    for D in diffusion_coeff:
        print(f"\n--- D = {D:.0e} m²/s ---")
        solver = TransportSolver(net, diffusion_coefficient=D)

        J_in = 1.0  # 1 mol/s injection
        success = solver.solve_concentration_distribution(J_source=J_in, C_sink=0.0)

        if success:
            solver.print_transport_metrics()
        else:
            print("  Solver failed")


def experiment4_transport_temperature_dependent():
    """Experiment 4: Temperature-dependent diffusion."""
    print("\n" + "=" * 60)
    print("EXPERIMENT 4: Temperature-Dependent Diffusion")
    print("=" * 60)

    net = create_test_network_phase5()

    print("\nDiffusion coefficients at different temperatures:")
    temperatures = [283.15, 293.15, 303.15, 313.15]

    for T in temperatures:
        D = WATER.diffusion_coefficient(T)
        print(f"  T = {T-273.15:.0f}°C: D = {D:.2e} m²/s")

    # Simulate transport at different temperatures
    print("\nTransport efficiency vs temperature:")

    for T in temperatures:
        D = WATER.diffusion_coefficient(T)
        solver = TransportSolver(net, diffusion_coefficient=D)
        success = solver.solve_concentration_distribution(J_source=1.0, C_sink=0.0)

        if success:
            metrics = solver.get_transport_metrics()
            print(f"\n  T = {T-273.15:.0f}°C")
            print(f"    R_eff (diffusion) = {metrics['R_eff_diffusion']:.2e}")
            print(f"    Concentration uniformity = {metrics['C_uniformity']:.2e}")


def experiment5_multi_physics_coupled():
    """Experiment 5: Coupled thermal-transport network."""
    print("\n" + "=" * 60)
    print("EXPERIMENT 5: Multi-Physics Coupling (Thermal + Transport)")
    print("=" * 60)

    net = create_test_network_phase5()

    print("\n--- Coupled Thermal-Transport Analysis ---")
    print("Scenario: Heat injection drives temperature-dependent diffusion")

    # Step 1: Solve thermal network
    thermal_solver = ThermalSolver(net, thermal_conductivity=0.6)
    Q_in = 100.0
    thermal_solver.solve_temperature_distribution(Q_source=Q_in, T_sink=300.0)

    print("\n1. Temperature Distribution (from thermal solver):")
    print(f"   Temperatures: {thermal_solver.temperatures}")

    # Step 2: Solve transport with temperature-dependent diffusion
    # Use spatially-averaged temperature for simplified coupling
    T_avg = np.mean(thermal_solver.temperatures)
    D_eff = WATER.diffusion_coefficient(T_avg)

    transport_solver = TransportSolver(net, diffusion_coefficient=D_eff)
    J_in = 1.0
    transport_solver.solve_concentration_distribution(J_source=J_in, C_sink=0.0)

    print("\n2. Transport with Temperature-Dependent Diffusion:")
    print(f"   Average temperature: {T_avg:.1f} K")
    print(f"   Effective diffusion coeff: {D_eff:.2e} m²/s")
    print(f"   Concentration distribution: {transport_solver.concentrations}")

    # Compute performance metrics
    print("\n3. Coupling Efficiency:")
    thermal_metrics = thermal_solver.get_thermal_metrics()
    transport_metrics = transport_solver.get_transport_metrics()

    print(f"\n   Thermal Performance:")
    print(f"     R_eff = {thermal_metrics['R_eff_thermal']:.4f} K/W")
    print(f"     T_uniformity = {thermal_metrics['T_uniformity']:.2e} K")

    print(f"\n   Transport Performance:")
    print(f"     R_eff = {transport_metrics['R_eff_diffusion']:.2e}")
    print(f"     C_uniformity = {transport_metrics['C_uniformity']:.2e}")

    # Coupling strength: correlation between temperature and concentration
    T_nonboundary = [
        thermal_solver.temperatures[i]
        for i in range(net.num_nodes)
        if i != net.source_id and i != net.sink_id
    ]
    C_nonboundary = [
        transport_solver.concentrations[i]
        for i in range(net.num_nodes)
        if i != net.source_id and i != net.sink_id
    ]

    if len(T_nonboundary) > 1:
        correlation = np.corrcoef(T_nonboundary, C_nonboundary)[0, 1]
        print(f"\n   Coupling Strength (T-C correlation): {correlation:.4f}")


def experiment6_constructal_principle_extended():
    """Experiment 6: Constructal principle with extended physics."""
    print("\n" + "=" * 60)
    print("EXPERIMENT 6: Constructal Principle with Extended Physics")
    print("=" * 60)

    net = create_test_network_phase5()

    print(
        "\nAnalyzing bottleneck dissipation across thermal and transport domains:"
    )

    # Thermal analysis
    thermal_solver = ThermalSolver(net, thermal_conductivity=0.6)
    thermal_solver.solve_temperature_distribution(Q_source=100.0, T_sink=300.0)

    print("\nThermal Dissipation by Channel:")
    for ch in thermal_solver.thermal_channels.values():
        if ch.heat_flow is not None:
            dissipation = abs(ch.heat_flow)
            R_ch = ch.thermal_resistance
            print(
                f"  Ch {ch.id}: Q={dissipation:.2f}W, R_th={R_ch:.4f}K/W, "
                f"dT={ch.delta_T:.2f}K"
            )

    # Transport analysis
    transport_solver = TransportSolver(net, diffusion_coefficient=1e-9)
    transport_solver.solve_concentration_distribution(J_source=1.0, C_sink=0.0)

    print("\nTransport Dissipation by Channel:")
    for ch in transport_solver.transport_channels.values():
        if ch.mass_flow is not None:
            # Dissipation analog: concentration drop
            print(
                f"  Ch {ch.id}: J={abs(ch.mass_flow):.2e}, R_diff={ch.diffusion_resistance:.2e}, "
                f"dC={ch.delta_C:.2e}"
            )

    # Identify bottlenecks
    print("\nBottleneck Analysis:")
    print("  Thermal: Channels with largest temperature drop")
    thermal_drops = [
        (ch.id, abs(ch.delta_T)) for ch in thermal_solver.thermal_channels.values()
        if ch.delta_T is not None
    ]
    thermal_drops.sort(key=lambda x: x[1], reverse=True)
    for ch_id, dT in thermal_drops[:2]:
        print(f"    Ch {ch_id}: dT = {dT:.2f}K")

    print("  Transport: Channels with largest concentration drop")
    transport_drops = [
        (ch.id, abs(ch.delta_C)) for ch in transport_solver.transport_channels.values()
        if ch.delta_C is not None
    ]
    transport_drops.sort(key=lambda x: x[1], reverse=True)
    for ch_id, dC in transport_drops[:2]:
        print(f"    Ch {ch_id}: dC = {dC:.2e}")


def run_all_phase5_experiments():
    """Run all Phase 5 experiments."""
    print("\n" + "=" * 70)
    print("PHASE 5: EXTENDED PHYSICS EXPERIMENTS")
    print("=" * 70)

    experiment1_thermal_basic()
    experiment2_thermal_temperature_dependent()
    experiment3_transport_basic()
    experiment4_transport_temperature_dependent()
    experiment5_multi_physics_coupled()
    experiment6_constructal_principle_extended()

    print("\n" + "=" * 70)
    print("ALL PHASE 5 EXPERIMENTS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_phase5_experiments()
