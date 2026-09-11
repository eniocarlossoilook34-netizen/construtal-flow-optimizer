"""Physical constants and fluid properties."""

import dataclasses


@dataclasses.dataclass
class FluidProperties:
    """Properties of the fluid (water-like, incompressible, Newtonian)."""

    viscosity: float = 1e-3  # Pa·s (dynamic viscosity, water at 20°C)
    density: float = 1000.0  # kg/m³

    def __post_init__(self):
        if self.viscosity <= 0:
            raise ValueError("Viscosity must be positive")
        if self.density <= 0:
            raise ValueError("Density must be positive")


class Constraints:
    """Physical and geometric constraints for the network."""

    # Channel geometry
    r_min = 0.01  # m (minimum radius, 1 cm)
    r_max = 0.5   # m (maximum radius, 50 cm)
    L_min = 0.1   # m (minimum length)
    L_max = 10.0  # m (maximum length)

    # Volume budget
    V_total = 1.0  # m³ (total material budget)

    # Pressure and flow limits
    P_max = 100_000  # Pa (pressure drop limit)
    v_max = 10.0  # m/s (velocity limit)

    # Numerical tolerance
    atol = 1e-6  # m³/s (flow continuity tolerance)
    P_tol = 1e-3  # Pa (pressure balance tolerance)
