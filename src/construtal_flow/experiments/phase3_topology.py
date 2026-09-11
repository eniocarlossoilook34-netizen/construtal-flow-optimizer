"""Phase 3 topological optimization experiments."""

from typing import Dict
import numpy as np
import matplotlib.pyplot as plt
from construtal_flow.network import Network
from construtal_flow.topology import (
    EvolutionaryTopology,
    ConstructalSearch,
    SimulatedTopologyAnnealing,
    TopologyValidator,
)


def create_free_topology_network() -> Network:
    """Test Case T1: Free topology (start with 1 channel)."""
    net = Network(num_nodes=3, source_id=0, sink_id=2)
    net.add_channel(0, 1, length=2.0, radius=0.05)
    net.add_channel(1, 2, length=2.0, radius=0.05)
    return net


def create_constrained_network() -> Network:
    """Test Case T2: Constrained volume (start with grid)."""
    net = Network(num_nodes=5, source_id=0, sink_id=4)
    # Create initial branching network
    net.add_channel(0, 1, length=1.0, radius=0.05)
    net.add_channel(1, 2, length=1.0, radius=0.05)
    net.add_channel(1, 3, length=1.0, radius=0.04)
    net.add_channel(2, 4, length=1.0, radius=0.05)
    net.add_channel(3, 4, length=1.0, radius=0.04)
    return net


def create_complex_network() -> Network:
    """Test Case T3: Complex branching."""
    net = Network(num_nodes=6, source_id=0, sink_id=5)
    net.add_channel(0, 1, length=1.0, radius=0.05)
    net.add_channel(1, 2, length=1.0, radius=0.04)
    net.add_channel(1, 3, length=1.0, radius=0.04)
    net.add_channel(2, 4, length=1.0, radius=0.03)
    net.add_channel(3, 4, length=1.0, radius=0.03)
    net.add_channel(4, 5, length=1.0, radius=0.05)
    return net


def run_topology_algorithm(
    network: Network,
    algorithm_class,
    algorithm_name: str,
    num_trials: int = 3,
    max_iterations: int = 30,
) -> Dict:
    """Run topology algorithm multiple times."""
    results_list = []

    for trial in range(num_trials):
        seed = trial * 1000
        optimizer = algorithm_class(
            network,
            max_iterations=max_iterations,
            seed=seed,
        )

        result = optimizer.optimize()
        results_list.append(result)

    # Aggregate
    objectives = [r.best_objective for r in results_list]
    channels = [r.final_channels for r in results_list]
    improvements = [(r.initial_objective - r.best_objective) / r.initial_objective * 100
                    for r in results_list]

    return {
        "algorithm": algorithm_name,
        "objectives": objectives,
        "channels": channels,
        "improvements": improvements,
        "mean_objective": np.mean(objectives),
        "std_objective": np.std(objectives),
        "mean_improvement": np.mean(improvements),
        "mean_channels": np.mean(channels),
        "best_result": min(results_list, key=lambda r: r.best_objective),
        "all_results": results_list,
    }


def run_phase3_experiments(max_iterations: int = 30, num_trials: int = 3) -> Dict:
    """Run all Phase 3 topological optimization experiments."""
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + " CONSTRUTAL FLOW OPTIMIZER — PHASE 3 TOPOLOGICAL EVOLUTION ".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)

    test_cases = {
        "free": ("Free Topology", create_free_topology_network()),
        "constrained": ("Constrained Volume", create_constrained_network()),
        "complex": ("Complex Branching", create_complex_network()),
    }

    algorithms = [
        (EvolutionaryTopology, "Evolutionary Topology"),
        (ConstructalSearch, "Constructal Search"),
        (SimulatedTopologyAnnealing, "Simulated Topology Annealing"),
    ]

    all_results = {}

    for case_name, (case_label, network) in test_cases.items():
        print(f"\n{'='*80}")
        print(f"Test Case: {case_label.upper()}")
        print(f"{'='*80}")

        # Validate initial network
        validation = TopologyValidator.validate_all(network)
        print(f"Initial network: {validation['num_channels']} channels, "
              f"{validation['num_nodes']} nodes")
        print(f"  Connected: {'✓' if validation['connected'] else '✗'}")
        print(f"  Acyclic: {'✓' if validation['acyclic'] else '✗'}")

        case_results = {}

        for algo_class, algo_name in algorithms:
            print(f"\n  Running {algo_name}...")

            result = run_topology_algorithm(
                network,
                algo_class,
                algo_name,
                num_trials=num_trials,
                max_iterations=max_iterations,
            )

            case_results[algo_name] = result

            print(f"    Best objective:    {result['best_result'].best_objective:.4e}")
            print(f"    Mean ± Std:        {result['mean_objective']:.4e} ± {result['std_objective']:.4e}")
            print(f"    Improvement:       {result['mean_improvement']:.2f}%")
            print(f"    Final channels:    {result['mean_channels']:.1f}")

        all_results[case_name] = case_results

    return all_results


def create_convergence_plots(all_results: Dict, output_path: str = "phase3_convergence.png"):
    """Create convergence plots for topological evolution."""
    test_cases = list(all_results.keys())
    n_cases = len(test_cases)

    fig, axes = plt.subplots(1, n_cases, figsize=(15, 5))
    if n_cases == 1:
        axes = [axes]

    colors = ["#FF6B6B", "#4ECDC4", "#45B7D1"]

    for ax, case_name in zip(axes, test_cases):
        case_results = all_results[case_name]

        ax.set_title(f"Test Case: {case_name.capitalize()}", fontsize=12, fontweight="bold")
        ax.set_xlabel("Iterations", fontsize=11)
        ax.set_ylabel("Best Objective Value", fontsize=11)
        ax.grid(alpha=0.3)

        for (algo_name, result), color in zip(case_results.items(), colors):
            best_result = result["best_result"]
            ax.plot(
                best_result.history_best,
                label=algo_name,
                linewidth=2,
                color=color,
                alpha=0.8,
            )

        ax.legend(fontsize=10)
        ax.set_yscale("log")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\n✓ Convergence plots saved to: {output_path}")
    return fig


def create_topology_comparison(all_results: Dict, output_path: str = "phase3_topology.png"):
    """Create topology comparison plots."""
    test_cases = list(all_results.keys())
    n_cases = len(test_cases)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    x_offset = 0
    width = 0.25
    colors = ["#FF6B6B", "#4ECDC4", "#45B7D1"]

    for case_idx, case_name in enumerate(test_cases):
        case_results = all_results[case_name]

        algo_names = list(case_results.keys())
        objectives = [case_results[name]["mean_objective"] for name in algo_names]
        channels = [case_results[name]["mean_channels"] for name in algo_names]

        x = np.arange(len(algo_names)) + case_idx * (width + 0.02)

        ax1.bar(x, objectives, width, label=case_name.capitalize(),
                color=colors[case_idx], alpha=0.8, edgecolor="black")

        ax2.bar(x, channels, width, label=case_name.capitalize(),
                color=colors[case_idx], alpha=0.8, edgecolor="black")

    ax1.set_ylabel("Resistance (Pa·s/m³)", fontsize=11)
    ax1.set_title("Final Resistance", fontsize=12, fontweight="bold")
    ax1.set_xticks(np.arange(3) * (width * 3 + 0.1) + width)
    ax1.set_xticklabels([a[1] for a in [(None, "ET"), (None, "CS"), (None, "STA")]])
    ax1.grid(axis="y", alpha=0.3)
    ax1.legend()

    ax2.set_ylabel("Number of Channels", fontsize=11)
    ax2.set_title("Final Network Structure", fontsize=12, fontweight="bold")
    ax2.set_xticks(np.arange(3) * (width * 3 + 0.1) + width)
    ax2.set_xticklabels([a[1] for a in [(None, "ET"), (None, "CS"), (None, "STA")]])
    ax2.grid(axis="y", alpha=0.3)
    ax2.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"✓ Topology comparison plots saved to: {output_path}")
    return fig


def print_summary(all_results: Dict):
    """Print summary table of results."""
    print("\n" + "=" * 100)
    print("PHASE 3 TOPOLOGICAL OPTIMIZATION SUMMARY")
    print("=" * 100)

    for case_name, case_results in all_results.items():
        print(f"\n{case_name.upper()}:")
        print("-" * 100)
        print(f"{'Algorithm':<30} {'Best Obj':<15} {'Mean ± Std':<25} {'Improvement':<15} {'Channels':<10}")
        print("-" * 100)

        for algo_name, result in case_results.items():
            best = result["best_result"].best_objective
            mean = result["mean_objective"]
            std = result["std_objective"]
            improvement = result["mean_improvement"]
            channels = result["mean_channels"]

            print(f"{algo_name:<30} {best:<15.4e} {mean:.4e} ± {std:.4e}  "
                  f"{improvement:>6.2f}%      {channels:>6.1f}")

        print()


if __name__ == "__main__":
    results = run_phase3_experiments(max_iterations=30, num_trials=3)
    print_summary(results)

    # Create plots
    create_convergence_plots(results, "phase3_convergence.png")
    create_topology_comparison(results, "phase3_topology.png")

    print("\n" + "=" * 80)
    print("Phase 3 experiments complete!")
    print("=" * 80)
