# Contributing to Construtal Flow Optimizer

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Focus on science and evidence
- Admit mistakes and learn from them
- Value reproducibility and correctness

## How to Contribute

### 1. Fork & Clone

```bash
git clone https://github.com/yourusername/construtal-flow-optimizer.git
cd construtal-flow-optimizer
git checkout -b feature/your-feature-name
```

### 2. Set Up Development Environment

```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-xdist

# Install in development mode
pip install -e .
```

### 3. Make Changes

- Write clean, readable code
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Add docstrings for all functions/classes
- Keep functions focused and testable

### 4. Write Tests

Every contribution needs tests:

```bash
# Write tests in tests/test_*.py
pytest tests/ -v              # Run all tests
pytest --cov=construtal_flow  # Coverage report
```

Target: **>90% code coverage** for new code

### 5. Commit & Push

```bash
git add .
git commit -m "Brief description of change

Optional detailed explanation explaining:
- What was changed
- Why it was changed
- How it was tested
"

git push origin feature/your-feature-name
```

### 6. Create Pull Request

- Clear title and description
- Reference related issues (#123)
- Link to any relevant documentation
- Include before/after examples if applicable

## Priority Contribution Areas

### High Priority

1. **Natural Network Validation**
   - River system data (bifurcation ratios, scaling)
   - Vascular network analysis (arteries, capillaries)
   - Bronchial tree geometry validation
   - Compare evolved networks to biological systems

2. **Scaling Laws**
   - **Horton's Laws** for river networks (bifurcation, length, area ratios)
   - **Murray's Law** for vascular branching optimization
   - Implement in optimization objectives

3. **Visualization & Analysis**
   - 3D network rendering
   - Flow field animations
   - Pareto frontier interactive plots
   - Bottleneck heat maps

### Medium Priority

4. **Performance & Scalability**
   - GPU acceleration (CuPy, JAX)
   - Sparse matrix optimizations
   - Parallel NSGA-II population evolution
   - Benchmark suite for regression testing

5. **Advanced Physics**
   - Turbulence models (Reynolds number effects)
   - Non-Newtonian fluid models
   - Compressible flow
   - Reactive transport
   - Multi-phase flow

### Lower Priority

6. **Machine Learning Integration**
   - Neural network surrogate models
   - Generative models for network design
   - Reinforcement learning for topology search
   - Transfer learning from natural networks

## Code Style Guide

### Python Style

```python
"""Module docstring explaining purpose."""

def calculate_hagen_poiseuille_resistance(
    length: float,
    radius: float,
    viscosity: float = 1e-3,
) -> float:
    """Calculate hydraulic resistance using Hagen-Poiseuille equation.

    Args:
        length: Channel length in meters
        radius: Channel radius in meters
        viscosity: Dynamic viscosity in Pa·s (default: water)

    Returns:
        Hydraulic resistance in Pa·s/m³

    Raises:
        ValueError: If radius or length <= 0

    Example:
        >>> R = calculate_hagen_poiseuille_resistance(1.0, 0.01)
        >>> print(f"{R:.2e}")
    """
    if radius <= 0 or length <= 0:
        raise ValueError("Radius and length must be positive")

    area = np.pi * radius ** 2
    return 8 * viscosity * length / (np.pi * radius ** 4)
```

### Class Structure

```python
class ThermalNetwork:
    """Represent and solve thermal networks.

    Attributes:
        network: Underlying hydraulic network (geometry)
        conductivity: Material thermal conductivity (W/(m·K))
        temperatures: Solution array of node temperatures (K)
    """

    def __init__(self, network: Network, conductivity: float):
        """Initialize thermal network.

        Args:
            network: Network geometry
            conductivity: Thermal conductivity
        """
        self.network = network
        self.conductivity = conductivity
        self.temperatures = np.zeros(network.num_nodes)

    def solve(self, Q_source: float = 100.0, T_sink: float = 300.0) -> bool:
        """Solve temperature distribution.

        Args:
            Q_source: Heat injection at source (W)
            T_sink: Reference temperature at sink (K)

        Returns:
            True if solver converged, False otherwise
        """
        # Implementation...
        pass
```

## Testing Standards

### Minimum Coverage

- New code: >90% coverage
- Bug fixes: Include regression test
- Refactors: Maintain or improve coverage

### Test Organization

```python
class TestHagenPoiseuille:
    """Test Hagen-Poiseuille physics implementation."""

    def test_resistance_formula(self):
        """Test basic resistance calculation."""
        # Arrange
        L, r, mu = 1.0, 0.01, 1e-3

        # Act
        R = calculate_hagen_poiseuille_resistance(L, r, mu)

        # Assert
        expected = 8 * mu * L / (np.pi * r ** 4)
        assert np.isclose(R, expected)

    def test_radius_fourth_power_dependence(self):
        """Verify R ∝ 1/r⁴ scaling."""
        # Test that doubling radius reduces R by factor of 2^4
        pass

    def test_invalid_inputs(self):
        """Test error handling for invalid inputs."""
        with pytest.raises(ValueError):
            calculate_hagen_poiseuille_resistance(-1.0, 0.01, 1e-3)
```

## Documentation Requirements

### For New Features

1. **Docstring:** Full function/class documentation
2. **Example:** Usage example in docstring
3. **Theory:** Mathematical background in docs/
4. **Experiment:** Demo in phase experiments
5. **Test:** Unit tests with >90% coverage

### For Bug Fixes

1. **Minimal reproduction:** Test case demonstrating bug
2. **Root cause:** Explanation in PR
3. **Verification:** Test passing after fix

## Commit Message Convention

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:** feat, fix, docs, refactor, test, perf, chore

**Scopes:** physics, solver, optimization, topology, multi_objective, visualization, tests

**Examples:**

```
feat(physics): add compressible flow support

Implement Mach number effects and pressure-dependent density.
Adds CompressibleChannel class and updated solver.

Closes #456
```

```
fix(solver): handle ill-conditioned matrices

Use regularization for near-singular matrices (rcond < 1e-15).
Adds tolerance parameter to LinearSolver.

Fixes #123
```

## Running the Full Test Suite

```bash
# Unit tests
pytest tests/ -v

# Coverage
pytest --cov=construtal_flow --cov-report=html

# All experiments
python -m construtal_flow.experiments.phase1_experiments
python -m construtal_flow.experiments.phase2_optimization
python -m construtal_flow.experiments.phase3_topology
python -m construtal_flow.experiments.phase5_experiments

# Check code style
flake8 src/ tests/
```

## Performance Expectations

- **Network creation:** O(n) - < 1 ms for 1000 nodes
- **Linear solver:** O(n³) - ~50 ms for 1000 nodes
- **Pareto frontier:** O(n²·g) - ~5 s for 100 gen, 100 nodes

Significant deviations need explanation in PR.

## Documentation Site

Documentation lives in:
- `docs/THEORY.md` - Physics foundations
- `docs/CONSTRUCTAL_LAW.md` - Constructal principle
- `docs/ALGORITHM_GUIDE.md` - Optimization algorithms
- `PHASE*_SUMMARY.md` - Phase-specific documentation
- Inline docstrings for API reference

## Questions?

- Open an Issue for questions
- Create a Discussion for design decisions
- Email: maintainer contact info

## Recognition

Contributors will be recognized in:
- GitHub contributor page
- Project documentation
- Citation acknowledgments

Thank you for contributing! 🙏
