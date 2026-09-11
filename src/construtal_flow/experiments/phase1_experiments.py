"""Phase 1 validation experiments: Series, Parallel, and Branching."""

import numpy as np
import matplotlib.pyplot as plt
from construtal_flow.network import Network
from construtal_flow.solver import LinearSolver


def experiment_series():
    """
    Experiment A: Series channels.

    Tests: Do three channels in series give R_eff = R1 + R2 + R3?
    """
    print("\n" + "="*70)
    print("EXPERIMENT A: SERIES CHANNELS")
    print("="*70)

    net = Network(num_nodes=4, source_id=0, sink_id=3)

    # Three identical channels in series
    r = 0.05  # m
    L = 1.0   # m

    net.add_channel(0, 1, length=L, radius=r)
    net.add_channel(1, 2, length=L, radius=r)
    net.add_channel(2, 3, length=L, radius=r)

    # Solve
    solver = LinearSolver(net)
    pressures, converged = solver.solve()

    if not converged:
        print("ERROR: Solver did not converge")
        return None

    if not solver.validate_solution():
        print("ERROR: Solution validation failed")
        return None

    # Analytical
    ch = net.get_channel(0)
    R_single = ch.resistance
    R_total_analytical = 3 * R_single

    # Computed
    metrics = net.get_network_metrics()
    R_eff = metrics["R_eff"]

    relative_error = abs(R_eff - R_total_analytical) / R_total_analytical

    print(f"Channel properties:")
    print(f"  Radius: {r} m")
    print(f"  Length (each): {L} m")
    print(f"  Single channel R: {R_single:.4e} Pa·s/m³")
    print(f"\nResults:")
    print(f"  Analytical R_total: {R_total_analytical:.4e} Pa·s/m³")
    print(f"  Computed R_eff:    {R_eff:.4e} Pa·s/m³")
    print(f"  Relative error:    {relative_error*100:.4f}%")
    print(f"  ✓ PASS" if relative_error < 0.01 else "  ✗ FAIL")

    print(f"\nFlow distribution:")
    for ch_id, ch in net.channels.items():
        print(f"  Channel {ch_id}: Q = {ch.Q:.6f} m³/s, ΔP = {ch.delta_P:.2f} Pa")

    print(f"\nPressures:")
    for i, P in enumerate(pressures):
        print(f"  Node {i}: P = {P:.2f} Pa")

    return {
        "name": "Series",
        "R_analytical": R_total_analytical,
        "R_computed": R_eff,
        "error": relative_error,
        "network": net,
    }


def experiment_parallel():
    """
    Experiment B: Parallel channels.

    Tests: Do two parallel channels give R_eff = R_single / 2?
    """
    print("\n" + "="*70)
    print("EXPERIMENT B: PARALLEL CHANNELS")
    print("="*70)

    net = Network(num_nodes=2, source_id=0, sink_id=1)

    # Two identical parallel branches
    r = 0.05  # m
    L = 1.0   # m

    net.add_channel(0, 1, length=L, radius=r)
    net.add_channel(0, 1, length=L, radius=r)

    # Solve
    solver = LinearSolver(net)
    pressures, converged = solver.solve()

    if not converged:
        print("ERROR: Solver did not converge")
        return None

    if not solver.validate_solution():
        print("ERROR: Solution validation failed")
        return None

    # Analytical
    ch = net.get_channel(0)
    R_single = ch.resistance
    R_total_analytical = R_single / 2.0

    # Computed
    metrics = net.get_network_metrics()
    R_eff = metrics["R_eff"]

    relative_error = abs(R_eff - R_total_analytical) / R_total_analytical

    print(f"Channel properties:")
    print(f"  Radius: {r} m")
    print(f"  Length (each): {L} m")
    print(f"  Single channel R: {R_single:.4e} Pa·s/m³")
    print(f"\nResults:")
    print(f"  Analytical R_total: {R_total_analytical:.4e} Pa·s/m³")
    print(f"  Computed R_eff:    {R_eff:.4e} Pa·s/m³")
    print(f"  Relative error:    {relative_error*100:.4f}%")
    print(f"  ✓ PASS" if relative_error < 0.01 else "  ✗ FAIL")

    print(f"\nFlow distribution:")
    for ch_id, ch in net.channels.items():
        print(f"  Channel {ch_id}: Q = {ch.Q:.6f} m³/s, ΔP = {ch.delta_P:.2f} Pa")

    print(f"\nPressures:")
    for i, P in enumerate(pressures):
        print(f"  Node {i}: P = {P:.2f} Pa")

    return {
        "name": "Parallel",
        "R_analytical": R_total_analytical,
        "R_computed": R_eff,
        "error": relative_error,
        "network": net,
    }


def experiment_branching():
    """
    Experiment C: Branching network.

    Network:
        0 (source) -> 1 (junction) -> 3 (sink)
                   -> 2 (branch) -|

    Tests: Flow conservation and pressure balance.
    """
    print("\n" + "="*70)
    print("EXPERIMENT C: BRANCHING NETWORK")
    print("="*70)

    net = Network(num_nodes=4, source_id=0, sink_id=3)

    # Main path: 0 -> 1 -> 3
    ch1_id = net.add_channel(0, 1, length=1.0, radius=0.05)
    ch3_id = net.add_channel(1, 3, length=1.0, radius=0.05)

    # Branch: 1 -> 2 -> 3
    ch2_id = net.add_channel(1, 2, length=1.0, radius=0.04)
    ch4_id = net.add_channel(2, 3, length=1.0, radius=0.04)

    # Solve
    solver = LinearSolver(net)
    pressures, converged = solver.solve()

    if not converged:
        print("ERROR: Solver did not converge")
        return None

    if not solver.validate_solution():
        print("ERROR: Solution validation failed")
        return None

    metrics = net.get_network_metrics()
    R_eff = metrics["R_eff"]

    print(f"Network topology:")
    print(f"  Nodes: 0 (source) -> 1 (junction) -> 3 (sink)")
    print(f"         1 (junction) -> 2 (branch) -> 3 (sink)")
    print(f"\nResults:")
    print(f"  R_eff: {R_eff:.4e} Pa·s/m³")
    print(f"  P_diss_total: {metrics['P_diss_total']:.4e} W")
    print(f"  Volume: {metrics['volume']:.6f} m³")

    print(f"\nFlow distribution:")
    for ch_id, ch in net.channels.items():
        print(f"  Channel {ch_id}: Q = {ch.Q:.6f} m³/s, ΔP = {ch.delta_P:.2f} Pa")

    print(f"\nPressures:")
    for i, P in enumerate(pressures):
        node_type = "source" if i == 0 else ("sink" if i == 3 else "junction")
        print(f"  Node {i} ({node_type}): P = {P:.2f} Pa")

    # Verify conservation at junction (node 1)
    ch1 = net.get_channel(ch1_id)
    ch2 = net.get_channel(ch2_id)
    ch3 = net.get_channel(ch3_id)

    Q_in = ch1.Q
    Q_out = ch2.Q + ch3.Q
    conservation_error = abs(Q_in - Q_out)

    print(f"\nFlow conservation at junction (node 1):")
    print(f"  Q_in: {Q_in:.6f} m³/s")
    print(f"  Q_out: {Q_out:.6f} m³/s")
    print(f"  Error: {conservation_error:.2e} m³/s")
    print(f"  ✓ PASS" if conservation_error < 1e-6 else "  ✗ FAIL")

    return {
        "name": "Branching",
        "R_eff": R_eff,
        "conservation_error": conservation_error,
        "network": net,
    }


def create_comparison_plot(results):
    """Create a comparison plot of all experiments."""
    if not all(results):
        print("Cannot create comparison plot: Missing results")
        return

    experiments = ["Series", "Parallel"]
    errors = [r["error"] * 100 for r in results[:2]]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Error comparison
    ax1.bar(experiments, errors, color=["#00CCFF", "#00FF88"], alpha=0.8, edgecolor="black")
    ax1.axhline(y=1.0, color="red", linestyle="--", label="1% threshold")
    ax1.set_ylabel("Relative Error (%)", fontsize=12, fontweight="bold")
    ax1.set_title("Validation: Analytical vs Computed", fontsize=13, fontweight="bold")
    ax1.set_ylim([0, max(2, max(errors) * 1.2)])
    ax1.legend()
    ax1.grid(axis="y", alpha=0.3)

    # Resistance comparison
    R_analytical = [r["R_analytical"] for r in results[:2]]
    R_computed = [r["R_computed"] for r in results[:2]]

    x = np.arange(len(experiments))
    width = 0.35

    ax2.bar(x - width/2, R_analytical, width, label="Analytical",
            color="#FF6600", alpha=0.8, edgecolor="black")
    ax2.bar(x + width/2, R_computed, width, label="Computed",
            color="#0066FF", alpha=0.8, edgecolor="black")

    ax2.set_ylabel("Resistance (Pa·s/m³)", fontsize=12, fontweight="bold")
    ax2.set_title("Effective Resistance Comparison", fontsize=13, fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(experiments)
    ax2.legend()
    ax2.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    return fig


def run_all_experiments():
    """Run all Phase 1 validation experiments."""
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + " CONSTRUTAL FLOW OPTIMIZER — PHASE 1 VALIDATION EXPERIMENTS ".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)

    results = [
        experiment_series(),
        experiment_parallel(),
        experiment_branching(),
    ]

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    for result in results:
        if result:
            if "error" in result:
                status = "✓ PASS" if result["error"] < 0.01 else "✗ FAIL"
                print(f"{result['name']:15} | Error: {result['error']*100:7.4f}% | {status}")
            else:
                print(f"{result['name']:15} | Validation successful")

    print("\n" + "="*70)
    print("All validation experiments completed.")
    print("="*70 + "\n")

    return results


if __name__ == "__main__":
    results = run_all_experiments()

    # Create and show plots
    fig = create_comparison_plot(results)
    if fig:
        plt.savefig("phase1_validation.png", dpi=150, bbox_inches="tight")
        print("Plot saved to: phase1_validation.png")
        plt.show()
