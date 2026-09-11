"""Extended physics module: Thermal, transport, electrical networks."""

from .thermal_network import ThermalChannel, ThermalSolver
from .transport_network import TransportChannel, TransportSolver
from .material_properties import MaterialProperties

__all__ = [
    "ThermalChannel",
    "ThermalSolver",
    "TransportChannel",
    "TransportSolver",
    "MaterialProperties",
]
