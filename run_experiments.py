"""Run Phase 1 experiments without interactive plot."""

import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

sys.path.insert(0, str(Path(__file__).parent / "src"))

import matplotlib.pyplot as plt
from construtal_flow.experiments import run_all_experiments
from construtal_flow.experiments.phase1_experiments import create_comparison_plot


if __name__ == "__main__":
    # Run experiments
    results = run_all_experiments()

    # Create plots
    fig = create_comparison_plot(results)

    if fig:
        output_path = Path(__file__).parent / "results" / "phase1_validation.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"\n✓ Plot saved to: {output_path}")

    plt.close('all')
