"""Run Phase 3 topological evolution experiments."""

import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')

sys.path.insert(0, str(Path(__file__).parent / "src"))

import matplotlib.pyplot as plt
from construtal_flow.experiments.phase3_topology import (
    run_phase3_experiments,
    create_convergence_plots,
    create_topology_comparison,
    print_summary,
)


if __name__ == "__main__":
    print("Running Phase 3 topological evolution experiments...")

    # Run experiments (reduced iterations for faster testing)
    results = run_phase3_experiments(max_iterations=20, num_trials=2)

    # Print summary
    print_summary(results)

    # Create plots directory
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate plots
    convergence_path = output_dir / "phase3_convergence.png"
    comparison_path = output_dir / "phase3_topology.png"

    create_convergence_plots(results, str(convergence_path))
    create_topology_comparison(results, str(comparison_path))

    plt.close('all')

    print("\n" + "="*80)
    print("✓ Phase 3 experiments complete!")
    print("="*80)
    print(f"\nResults saved to:")
    print(f"  - {convergence_path}")
    print(f"  - {comparison_path}")
