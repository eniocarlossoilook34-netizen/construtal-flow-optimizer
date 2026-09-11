"""Run Phase 2 optimization experiments."""

import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')

sys.path.insert(0, str(Path(__file__).parent / "src"))

import matplotlib.pyplot as plt
from construtal_flow.experiments.phase2_optimization import (
    run_phase2_experiments,
    create_convergence_plots,
    create_comparison_bars,
    print_summary,
)


if __name__ == "__main__":
    # Run experiments
    print("Running Phase 2 optimization experiments...")
    results = run_phase2_experiments(max_iterations=100, num_trials=5)

    # Print summary
    print_summary(results)

    # Create plots directory
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate plots
    convergence_path = output_dir / "phase2_convergence.png"
    comparison_path = output_dir / "phase2_comparison.png"

    create_convergence_plots(results, str(convergence_path))
    create_comparison_bars(results, str(comparison_path))

    plt.close('all')

    print("\n" + "="*80)
    print("✓ Phase 2 experiments complete!")
    print("="*80)
    print(f"\nResults saved to:")
    print(f"  - {convergence_path}")
    print(f"  - {comparison_path}")
