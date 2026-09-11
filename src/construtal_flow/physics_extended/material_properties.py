"""Material properties: Temperature-dependent fluid and solid material parameters."""

from dataclasses import dataclass
import numpy as np


@dataclass
class MaterialProperties:
    """Material properties with temperature-dependent models."""

    name: str
    temperature_ref: float = 293.15  # Reference temperature (K, ~20°C)

    # Base properties at reference temperature
    viscosity_ref: float = 1e-3  # Pa·s
    thermal_conductivity_ref: float = 0.6  # W/(m·K)
    diffusion_coefficient_ref: float = 1e-9  # m²/s
    density_ref: float = 1000.0  # kg/m³

    # Temperature dependence coefficients
    viscosity_alpha: float = 0.03  # Temperature coefficient (1/K) for viscosity
    thermal_conductivity_alpha: float = 0.002  # Temperature coefficient for k
    diffusion_alpha: float = 0.01  # Temperature coefficient for D

    def viscosity(self, T: float) -> float:
        """
        Compute viscosity at temperature T.

        Exponential model: μ(T) = μ_ref * exp(α * (T - T_ref))
        """
        return self.viscosity_ref * np.exp(
            self.viscosity_alpha * (T - self.temperature_ref)
        )

    def thermal_conductivity(self, T: float) -> float:
        """
        Compute thermal conductivity at temperature T.

        Linear model: k(T) = k_ref * (1 + α * (T - T_ref))
        """
        return self.thermal_conductivity_ref * (
            1.0 + self.thermal_conductivity_alpha * (T - self.temperature_ref)
        )

    def diffusion_coefficient(self, T: float) -> float:
        """
        Compute diffusion coefficient at temperature T.

        Power law (Arrhenius-like): D(T) = D_ref * (T / T_ref)^α
        """
        return self.diffusion_coefficient_ref * (T / self.temperature_ref) ** (
            self.diffusion_alpha
        )

    def density(self, T: float) -> float:
        """
        Compute density at temperature T.

        Linear approximation: ρ(T) = ρ_ref * (1 - β * (T - T_ref))
        where β is thermal expansion coefficient
        """
        thermal_expansion = 2e-4  # 1/K for water
        return self.density_ref * (
            1.0 - thermal_expansion * (T - self.temperature_ref)
        )

    def __repr__(self) -> str:
        return (
            f"MaterialProperties(name={self.name}, "
            f"μ={self.viscosity_ref:.2e} Pa·s, "
            f"k={self.thermal_conductivity_ref:.2f} W/(m·K), "
            f"D={self.diffusion_coefficient_ref:.2e} m²/s)"
        )


# Common material presets
WATER = MaterialProperties(
    name="Water",
    temperature_ref=293.15,
    viscosity_ref=1e-3,
    thermal_conductivity_ref=0.6,
    diffusion_coefficient_ref=1e-9,
    density_ref=1000.0,
    viscosity_alpha=-0.03,  # Negative: viscosity decreases with temperature
    thermal_conductivity_alpha=0.002,
    diffusion_alpha=0.01,
)

GLYCERIN = MaterialProperties(
    name="Glycerin",
    temperature_ref=293.15,
    viscosity_ref=1.5,  # Much higher viscosity
    thermal_conductivity_ref=0.28,
    diffusion_coefficient_ref=0.5e-9,
    density_ref=1260.0,
    viscosity_alpha=0.05,  # More temperature-sensitive
    thermal_conductivity_alpha=0.0005,
    diffusion_alpha=0.015,
)

AIR = MaterialProperties(
    name="Air",
    temperature_ref=293.15,
    viscosity_ref=1.8e-5,  # Much lower viscosity
    thermal_conductivity_ref=0.026,
    diffusion_coefficient_ref=2.5e-5,  # Much higher diffusion
    density_ref=1.2,
    viscosity_alpha=0.007,
    thermal_conductivity_alpha=0.004,
    diffusion_alpha=0.08,
)

SILICON_OIL = MaterialProperties(
    name="Silicon Oil",
    temperature_ref=293.15,
    viscosity_ref=0.02,
    thermal_conductivity_ref=0.16,
    diffusion_coefficient_ref=0.8e-9,
    density_ref=960.0,
    viscosity_alpha=0.04,
    thermal_conductivity_alpha=0.0003,
    diffusion_alpha=0.012,
)
