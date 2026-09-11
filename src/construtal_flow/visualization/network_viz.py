"""Network visualization: Draw hydraulic flow networks."""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import LineCollection
from construtal_flow.network import Network
from construtal_flow.multi_objective.objectives import ObjectiveSet


class NetworkVisualizer:
    """Visualize hydraulic flow networks with flow indicators."""

    def __init__(self, network: Network, figsize: tuple = (10, 8)):
        """
        Initialize visualizer.

        Args:
            network: Network to visualize
            figsize: Figure size (width, height)
        """
        self.network = network
        self.figsize = figsize

        # Compute node positions (hierarchical layout)
        self.node_positions = self._compute_hierarchical_layout()

    def _compute_hierarchical_layout(self) -> dict:
        """Compute node positions using hierarchical layout."""
        positions = {}

        # Source at bottom, sink at top
        positions[self.network.source_id] = np.array([0.5, 0.0])
        positions[self.network.sink_id] = np.array([0.5, 1.0])

        # Place intermediate nodes in middle layers
        intermediate_nodes = [
            n for n in range(self.network.num_nodes)
            if n != self.network.source_id and n != self.network.sink_id
        ]

        n_intermediate = len(intermediate_nodes)

        if n_intermediate > 0:
            y_layer = 0.5
            x_positions = np.linspace(0.1, 0.9, n_intermediate)

            for i, node in enumerate(sorted(intermediate_nodes)):
                positions[node] = np.array([x_positions[i], y_layer])

        return positions

    def draw_network(self, show_labels: bool = True, show_metrics: bool = True) -> plt.Figure:
        """
        Draw network diagram.

        Args:
            show_labels: Show node labels
            show_metrics: Show network metrics on plot

        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        # Compute colors and widths based on physics
        obj_set = ObjectiveSet(self.network)
        obj_set.compute_all()

        # Draw edges (channels)
        for ch in self.network.channels.values():
            pos_from = self.node_positions[ch.node_from]
            pos_to = self.node_positions[ch.node_to]

            # Width proportional to radius
            width = 2 + 15 * (ch.radius / 0.5)

            # Color based on dissipation
            if ch.Q is not None:
                dissipation = ch.compute_dissipated_power(ch.Q)
                # Normalize dissipation for color mapping
                color_intensity = min(dissipation / 1000, 1.0)
            else:
                color_intensity = 0.5

            # Blue (low) to red (high) colormap
            color = plt.cm.RdYlBu_r(color_intensity)

            ax.plot(
                [pos_from[0], pos_to[0]],
                [pos_from[1], pos_to[1]],
                color=color,
                linewidth=width,
                alpha=0.8,
                zorder=1,
            )

        # Draw nodes
        for node_id, pos in self.node_positions.items():
            # Size based on flow through node
            if node_id == self.network.source_id or node_id == self.network.sink_id:
                size = 500
                color = 'darkgreen' if node_id == self.network.source_id else 'darkred'
            else:
                size = 300
                color = 'steelblue'

            ax.scatter(*pos, s=size, c=color, alpha=0.8, zorder=2, edgecolors='black', linewidth=2)

            if show_labels:
                label = 'Source' if node_id == self.network.source_id else (
                    'Sink' if node_id == self.network.sink_id else f'Node {node_id}'
                )
                ax.text(pos[0], pos[1], label, ha='center', va='center', fontsize=9, fontweight='bold', zorder=3)

        # Set plot properties
        ax.set_xlim(-0.1, 1.1)
        ax.set_ylim(-0.1, 1.1)
        ax.set_aspect('equal')
        ax.axis('off')

        # Add title with metrics
        if show_metrics:
            metrics = self.network.get_network_metrics()
            title = f'Network: {len(self.network.channels)} channels | R_eff={metrics["R_eff"]:.2e} Pa·s/m³'
            ax.set_title(title, fontsize=12, fontweight='bold', pad=20)

        # Add colorbar for dissipation
        sm = plt.cm.ScalarMappable(cmap=plt.cm.RdYlBu_r, norm=plt.Normalize(vmin=0, vmax=1))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Dissipation (normalized)', fontsize=10)

        plt.tight_layout()
        return fig

    def save_figure(self, filepath: str):
        """
        Save network diagram to file.

        Args:
            filepath: Output file path
        """
        fig = self.draw_network()
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close(fig)

    @staticmethod
    def create_network_montage(networks: list, titles: list = None, figsize: tuple = (15, 10)) -> plt.Figure:
        """
        Create montage of multiple networks.

        Args:
            networks: List of Network objects
            titles: Optional titles for each network
            figsize: Figure size

        Returns:
            Matplotlib figure
        """
        n_networks = len(networks)
        n_cols = min(n_networks, 3)
        n_rows = (n_networks + n_cols - 1) // n_cols

        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)

        if n_networks == 1:
            axes = [[axes]]
        elif n_rows == 1:
            axes = [axes]

        for idx, net in enumerate(networks):
            row = idx // n_cols
            col = idx % n_cols

            ax = axes[row][col] if isinstance(axes[0], list) else axes[idx]

            # Draw network on this axis
            viz = NetworkVisualizer(net, figsize=(5, 5))
            fig_temp = viz.draw_network(show_labels=False)

            # Copy to subplot (simplified)
            metrics = net.get_network_metrics()
            title = titles[idx] if titles else f'Network {idx + 1}'
            ax.text(0.5, 0.5, title, ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.axis('off')

            plt.close(fig_temp)

        # Hide unused subplots
        for idx in range(n_networks, n_rows * n_cols):
            row = idx // n_cols
            col = idx % n_cols
            ax = axes[row][col] if isinstance(axes[0], list) else axes[idx]
            ax.axis('off')

        plt.tight_layout()
        return fig
