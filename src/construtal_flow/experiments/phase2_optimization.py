"""Phase 2 optimization experiments."""

from typing import Dict, List, Tuple
import numpy as np
import matplotlib.pyplot as plt
from construtal_flow.network import Network
from construtal_flow.optimization import (
    RandomSearch,
    GradientDescent,
    EvolutionaryAlgorithm,
    SimulatedAnnealing,
    ObjectiveType,
)


def create_test_networks() -> Dict[str, Network]:
    """Create the three test networks for Phase 2."""
    networks = {}

    # Network 1: Series (3 channels)
    net1 = Network(num_nodes=4, source_id=0, sink_id=3)
    net1.add_channel(0, 1, length=1.0, radius=0.05)
    net1.add_channel(1, 2, length=1.0, radius=0.05)
    net1.add_channel(2, 3, length=1.0, radius=0.05)
    networks["series"] = net1

    # Network 2: Parallel (2 channels)
    net2 = Network(num_nodes=2, source_id=0, sink_id=1)
    net2.add_channel(0, 1, length=1.0, radius=0.05)
    net2.add_channel(0, 1, length=1.0, radius=0.05)
    networks["parallel"] = net2

    # Network 3: Branching (4 channels)
    net3 = Network(num_nodes=4, source_id=0, sink_id=3)
    net3.add_channel(0, 1, length=1.0, radius=0.05)
    net3.add_channel(1, 2, length=1.0, radius=0.04)
    net3.add_channel(1, 3, length=1.0, radius=0.05)
    net3.add_channel(2, 3, length=1.0, radius=0.04)
    networks["branching"] = net3

    return networks


def run_algorithm_on_network(
    network: Network,
    algorithm_class,
    algorithm_name: str,
    num_trials: int = 5,
    max_iterations: int = 100,
) -> Dict:
    """Run an algorithm on a network multiple times."""
    results_list = []

    for trial in range(num_trials):
        seed = trial * 1000
        optimizer = algorithm_class(
            network,
            obj_type=ObjectiveType.RESISTANCE,
            volume_budget=1.0,
            max_iterations=max_iterations,
            seed=seed,
        )

        result = optimizer.optimize()
        results_list.append(result)

    # Aggregate results
    objectives = [r.best_objective for r in results_list]
    improvements = [r.improvement_percent for r in results_list]

    return {
        "algorithm": algorithm_name,
        "objectives": objectives,
        "improvements": improvements,
        "mean_objective": np.mean(objectives),
        "std_objective": np.std(objectives),
        "mean_improvement": np.mean(improvements),
        "std_improvement": np.std(improvements),
        "best_result": min(results_list, key=lambda r: r.best_objective),
        "all_results": results_list,
    }


def run_phase2_experiments(max_iterations: int = 100, num_trials: int = 5) -> Dict:
    """Run all Phase 2 optimization experiments."""
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + " CONSTRUTAL FLOW OPTIMIZER — PHASE 2 OPTIMIZATION EXPERIMENTS ".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)

    networks = create_test_networks()
    algorithms = [
        (RandomSearch, "Random Search"),
        (GradientDescent, "Gradient Descent"),
        (EvolutionaryAlgorithm, "Evolutionary Algorithm"),
        (SimulatedAnnealing, "Simulated Annealing"),
    ]

    all_results = {}

    for net_name, network in networks.items():
        print(f"\n{'='*80}")
        print(f"Network: {net_name.upper()}")
        print(f"{'='*80}")
        print(f"Channels: {len(network.channels)}")
        print(f"Nodes: {network.num_nodes}")

        network_results = {}

        for algo_class, algo_name in algorithms:
            print(f"\n  Running {algo_name}...")
            result = run_algorithm_on_network(
                network,
                algo_class,
                algo_name,
                num_trials=num_trials,
                max_iterations=max_iterations,
            )
            network_results[algo_name] = result

            print(f"    Best objective:    {result['best_result'].best_objective:.4e}")
            print(f"    Mean ± Std:        {result['mean_objective']:.4e} ± {result['std_objective']:.4e}")
            print(f"    Improvement:       {result['mean_improvement']:.2f}% ± {result['std_improvement']:.2f}%")

        all_results[net_name] = network_results

    return all_results


def create_convergence_plots(all_results: Dict, output_path: str = "phase2_convergence.png"):
    """Create convergence plots for all networks and algorithms."""
    networks = list(all_results.keys())
    n_nets = len(networks)

    fig, axes = plt.subplots(1, n_nets, figsize=(15, 5))
    if n_nets == 1:
        axes = [axes]

    for ax, net_name in zip(axes, networks):
        network_results = all_results[net_name]

        ax.set_title(f"Network: {net_name.capitalize()}", fontsize=12, fontweight="bold")
        ax.set_xlabel("Iterations", fontsize=11)
        ax.set_ylabel("Best Objective Value", fontsize=11)
        ax.grid(alpha=0.3)

        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A"]

        for (algo_name, result), color in zip(network_results.items(), colors):
            # Get first trial's convergence history
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


def create_comparison_bars(all_results: Dict, output_path: str = "phase2_comparison.png"):
    """Create comparison bar charts for all algorithms."""
    networks = list(all_results.keys())
    n_nets = len(networks)

    fig, axes = plt.subplots(1, n_nets, figsize=(15, 5))
    if n_nets == 1:
        axes = [axes]

    for ax, net_name in zip(axes, networks):
        network_results = all_results[net_name]

        algo_names = list(network_results.keys())
        objectives = [network_results[name]["mean_objective"] for name in algo_names]
        std_devs = [network_results[name]["std_objective"] for name in algo_names]

        x = np.arange(len(algo_names))
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A"]

        bars = ax.bar(x, objectives, yerr=std_devs, capsize=5, color=colors[:len(algo_names)], alpha=0.8, edgecolor="black")

        ax.set_title(f"Network: {net_name.capitalize()}", fontsize=12, fontweight="bold")
        ax.set_ylabel("Resistance (Pa·s/m³)", fontsize=11)
        ax.set_xticks(x)
        ax.set_xticklabels(algo_names, rotation=45, ha="right", fontsize=9)
        ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"✓ Comparison plots saved to: {output_path}")
    return fig


def print_summary(all_results: Dict):
    """Print summary table of results."""
    print("\n" + "=" * 80)
    print("PHASE 2 OPTIMIZATION SUMMARY")
    print("=" * 80)

    for net_name, network_results in all_results.items():
        print(f"\n{net_name.upper()}:")
        print("-" * 80)
        print(f"{'Algorithm':<25} {'Best':<15} {'Mean ± Std':<25} {'Improvement (%)':<15}")
        print("-" * 80)

        for algo_name, result in network_results.items():
            best = result["best_result"].best_objective
            mean = result["mean_objective"]
            std = result["std_objective"]
            improvement = result["mean_improvement"]

            print(f"{algo_name:<25} {best:<15.4e} {mean:.4e} ± {std:.4e}  {improvement:>6.2f}%")

        print()


if __name__ == "__main__":
    results = run_phase2_experiments(max_iterations=100, num_trials=5)
    print_summary(results)

    # Create plots
    create_convergence_plots(results, "phase2_convergence.png")
    create_comparison_bars(results, "phase2_comparison.png")

    print("\n" + "=" * 80)
    print("Phase 2 experiments complete!")
    print("=" * 80)
