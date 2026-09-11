"""Pareto frontier visualization."""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from construtal_flow.multi_objective.pareto import ParetoFrontier


def create_pareto_plots(frontier: ParetoFrontier, output_path: str = None) -> plt.Figure:
    """
    Create multi-view Pareto frontier plots.

    Args:
        frontier: ParetoFrontier object
        output_path: Optional output file path

    Returns:
        Matplotlib figure
    """
    objectives = frontier.get_objectives_matrix()

    if len(objectives) == 0:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, 'Empty frontier', ha='center', va='center')
        return fig

    # Create subplots
    fig = plt.figure(figsize=(16, 10))

    # Plot 1: R_eff vs P_diss (2D)
    ax1 = plt.subplot(2, 3, 1)
    ax1.scatter(objectives[:, 0], objectives[:, 1], c=objectives[:, 2], cmap='viridis', s=100, alpha=0.6, edgecolors='black')
    ax1.set_xlabel('Effective Resistance R_eff (Pa·s/m³)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Dissipated Power P_diss (W)', fontsize=11, fontweight='bold')
    ax1.set_title('Pareto Front: Resistance vs Dissipation', fontsize=12, fontweight='bold')
    ax1.set_xscale('log')
    ax1.set_yscale('log')
    ax1.grid(True, alpha=0.3)
    cbar1 = plt.colorbar(ax1.collections[0], ax=ax1)
    cbar1.set_label('Volume (m³)', fontsize=10)

    # Plot 2: R_eff vs Volume (2D)
    ax2 = plt.subplot(2, 3, 2)
    scatter2 = ax2.scatter(objectives[:, 2], objectives[:, 0], c=objectives[:, 1], cmap='plasma', s=100, alpha=0.6, edgecolors='black')
    ax2.set_xlabel('Volume (m³)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Effective Resistance R_eff (Pa·s/m³)', fontsize=11, fontweight='bold')
    ax2.set_title('Pareto Front: Volume vs Resistance', fontsize=12, fontweight='bold')
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3)
    cbar2 = plt.colorbar(scatter2, ax=ax2)
    cbar2.set_label('Dissipation (W)', fontsize=10)

    # Plot 3: P_diss vs Volume (2D)
    ax3 = plt.subplot(2, 3, 3)
    scatter3 = ax3.scatter(objectives[:, 2], objectives[:, 1], c=objectives[:, 0], cmap='coolwarm', s=100, alpha=0.6, edgecolors='black')
    ax3.set_xlabel('Volume (m³)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Dissipated Power P_diss (W)', fontsize=11, fontweight='bold')
    ax3.set_title('Pareto Front: Volume vs Dissipation', fontsize=12, fontweight='bold')
    ax3.set_yscale('log')
    ax3.grid(True, alpha=0.3)
    cbar3 = plt.colorbar(scatter3, ax=ax3)
    cbar3.set_label('Resistance (Pa·s/m³)', fontsize=10)

    # Plot 4: 3D plot
    ax4 = plt.subplot(2, 3, 4, projection='3d')
    scatter4 = ax4.scatter(
        objectives[:, 0],  # R_eff
        objectives[:, 1],  # P_diss
        objectives[:, 2],  # Volume
        c=objectives[:, 3],  # Complexity (color)
        cmap='Spectral_r',
        s=100,
        alpha=0.6,
        edgecolors='black',
    )
    ax4.set_xlabel('R_eff (log)', fontsize=10, fontweight='bold')
    ax4.set_ylabel('P_diss (log)', fontsize=10, fontweight='bold')
    ax4.set_zlabel('Volume', fontsize=10, fontweight='bold')
    ax4.set_title('3D Pareto Front', fontsize=12, fontweight='bold')
    ax4.set_xscale('log')
    ax4.set_yscale('log')
    cbar4 = plt.colorbar(scatter4, ax=ax4, pad=0.1)
    cbar4.set_label('Complexity', fontsize=10)

    # Plot 5: Hypervolume progression (if available)
    ax5 = plt.subplot(2, 3, 5)
    ax5.text(0.5, 0.5, f'Frontier Size: {len(objectives)}\nHypervolume: {frontier.compute_hypervolume():.4e}',
             ha='center', va='center', fontsize=12, transform=ax5.transAxes, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    ax5.axis('off')
    ax5.set_title('Frontier Statistics', fontsize=12, fontweight='bold')

    # Plot 6: Objective ranges
    ax6 = plt.subplot(2, 3, 6)
    obj_names = ['R_eff\n(log)', 'P_diss\n(log)', 'Volume', 'Complexity']
    obj_mins = [np.log10(objectives[:, 0].min()), np.log10(objectives[:, 1].min()), objectives[:, 2].min(), objectives[:, 3].min()]
    obj_maxs = [np.log10(objectives[:, 0].max()), np.log10(objectives[:, 1].max()), objectives[:, 2].max(), objectives[:, 3].max()]

    x_pos = np.arange(len(obj_names))
    ax6.bar(x_pos, np.array(obj_maxs) - np.array(obj_mins), bottom=obj_mins, alpha=0.7, edgecolor='black', color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A'])
    ax6.set_xticks(x_pos)
    ax6.set_xticklabels(obj_names, fontsize=10)
    ax6.set_ylabel('Value range', fontsize=11, fontweight='bold')
    ax6.set_title('Objective Ranges', fontsize=12, fontweight='bold')
    ax6.grid(axis='y', alpha=0.3)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Saved Pareto plots to {output_path}")

    return fig


def plot_pareto_progression(history_frontier_size: list, history_hypervolume: list = None) -> plt.Figure:
    """
    Plot convergence of Pareto frontier.

    Args:
        history_frontier_size: Frontier size per generation
        history_hypervolume: Hypervolume per generation (optional)

    Returns:
        Matplotlib figure
    """
    fig, axes = plt.subplots(1, 2 if history_hypervolume else 1, figsize=(12, 4))

    if history_hypervolume is None:
        axes = [axes]

    # Plot 1: Frontier size
    ax1 = axes[0]
    ax1.plot(history_frontier_size, linewidth=2, color='#FF6B6B', marker='o', markersize=5)
    ax1.fill_between(range(len(history_frontier_size)), history_frontier_size, alpha=0.3, color='#FF6B6B')
    ax1.set_xlabel('Generation', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Frontier Size (# solutions)', fontsize=11, fontweight='bold')
    ax1.set_title('Pareto Frontier Growth', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # Plot 2: Hypervolume
    if history_hypervolume:
        ax2 = axes[1]
        ax2.plot(history_hypervolume, linewidth=2, color='#4ECDC4', marker='s', markersize=5)
        ax2.fill_between(range(len(history_hypervolume)), history_hypervolume, alpha=0.3, color='#4ECDC4')
        ax2.set_xlabel('Generation', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Hypervolume', fontsize=11, fontweight='bold')
        ax2.set_title('Frontier Quality (Hypervolume)', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig
