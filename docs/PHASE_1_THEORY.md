# Phase 1: Minimal Physical Model — Theory & Implementation

## Table of Contents

1. [Physical Model](#physical-model)
2. [Mathematical Formulation](#mathematical-formulation)
3. [Solution Method](#solution-method)
4. [Validation Strategy](#validation-strategy)
5. [Implementation Details](#implementation-details)
6. [Error Analysis](#error-analysis)

---

## Physical Model

### Regime and Assumptions

**Laminar, Incompressible, Steady-State Flow:**

```
ASSUMPTION 1:  Laminar flow (Re < 2300 for circular pipes)
               → Hagen-Poiseuille law applies
               
ASSUMPTION 2:  Incompressible fluid (ρ constant)
               → Continuity equation: ∇·v = 0
               
ASSUMPTION 3:  Steady-state flow (∂/∂t = 0)
               → Conservation laws reduce to algebraic equations
               
ASSUMPTION 4:  No gravity, no stratification
               
ASSUMPTION 5:  Newtonian fluid (constant viscosity μ)
               
ASSUMPTION 6:  Isothermal flow (T constant)
               → No heat transfer coupling
```

**These assumptions are valid for:**
- Water-like fluids at room temperature
- Slow flows in relatively large channels
- Short simulation durations
- Absence of thermal gradients

**These assumptions fail when:**
- Flow becomes turbulent (Re > 2300)
- High-speed flows (compressibility matters)
- Extreme temperature gradients
- Non-Newtonian fluids (blood, mud, polymers)

---

## Mathematical Formulation

### 1. Continuity Equation (Mass Conservation)

At each node (junction) in the network:

$$\sum_{\text{in}} Q_{\text{in}} = \sum_{\text{out}} Q_{\text{out}}$$

**Interpretation:** Volumetric flow is conserved at junctions. No fluid accumulation.

**For internal nodes (not source or sink):**

$$\sum_{i \in I(n)} Q_i - \sum_{j \in O(n)} Q_j = 0$$

where:
- $I(n)$ = incoming channels at node $n$
- $O(n)$ = outgoing channels at node $n$
- $Q_i$ = volumetric flow rate in channel $i$ (m³/s)

---

### 2. Hagen-Poiseuille Law

For laminar flow in a cylindrical channel:

$$\Delta P = R_h \cdot Q$$

where the **hydraulic resistance** is:

$$R_h = \frac{8\mu L}{\pi r^4}$$

**Derivation:** From the Navier-Stokes equations, assuming fully developed parabolic velocity profile.

**Parameters:**
- $\mu$ = dynamic viscosity (Pa·s)
- $L$ = channel length (m)
- $r$ = channel radius (m)
- $Q$ = volumetric flow rate (m³/s)
- $\Delta P$ = pressure drop (Pa)

**Validity:**
- Circular cross-section required (not rectangular, triangular, etc.)
- Laminar regime only (Re < 2300)
- Fully developed flow (entrance effects ignored)

---

### 3. Kirchhoff's Voltage Law for Flow Networks

The sum of pressure drops around any closed loop equals zero:

$$\sum_{\text{loop}} \Delta P_i = 0$$

This is analogous to Kirchhoff's voltage law in electrical circuits:
- Pressure ↔ Voltage
- Flow rate ↔ Current
- Resistance ↔ Resistance

**Consequence:** Node potentials (pressures) are well-defined and unique.

---

### 4. Nodal Analysis Formulation

We choose **nodal pressures** as unknowns: $P_0, P_1, \ldots, P_{n-1}$

For each channel $i \to j$:

$$Q_{ij} = \frac{P_i - P_j}{R_h^{ij}}$$

Apply continuity at each internal node $n$:

$$\sum_{i \in I(n)} Q_{in} = \sum_{j \in O(n)} Q_{nj}$$

Substitute the flow equations:

$$\sum_{i \in I(n)} \frac{P_i - P_n}{R_h^{in}} = \sum_{j \in O(n)} \frac{P_n - P_j}{R_h^{nj}}$$

Rearrange:

$$P_n \left( \sum_{i \in I(n)} \frac{1}{R_h^{in}} + \sum_{j \in O(n)} \frac{1}{R_h^{nj}} \right) = \sum_{i \in I(n)} \frac{P_i}{R_h^{in}} + \sum_{j \in O(n)} \frac{P_j}{R_h^{nj}}$$

**This is a linear system:** $G \cdot P = I$

where:
- $G$ = conductance matrix (sparse, symmetric)
- $P$ = vector of nodal pressures
- $I$ = current (flow injection/extraction) vector

---

### 5. Objective Functions

#### R_eff: Effective Network Resistance

$$R_{\text{eff}} = \frac{\Delta P_{\text{source} \to \text{sink}}}{Q_{\text{in}}}$$

**Interpretation:** How much pressure is needed to drive a unit flow through the network.

**Units:** Pa·s/m³

**Lower is better:** Easier to drive flow (less energy loss).

---

#### P_diss: Total Viscous Dissipation

$$P_{\text{diss}} = \sum_{\text{channels}} R_h \cdot Q^2$$

**Interpretation:** Total power dissipated as heat due to viscous friction.

**Units:** W (Watts)

**Derivation:** Power dissipated in channel $i$: $P_i = \Delta P_i \cdot Q_i = R_h \cdot Q^2$

**Lower is better:** Less energy wasted.

---

#### S_gen: Entropy Generation Rate

**Fundamental thermodynamic quantity (advanced, Phase 2+):**

$$\dot{S}_{\text{gen}} = \frac{P_{\text{diss}}}{T}$$

where $T$ = absolute temperature.

For isothermal flow, $P_{\text{diss}} \propto \dot{S}_{\text{gen}}$.

---

### 6. Key Derived Quantities

#### Velocity in a channel:

$$v = \frac{Q}{A} = \frac{Q}{\pi r^2}$$

#### Reynolds number (dimensionless, predicts laminar vs turbulent):

$$\text{Re} = \frac{\rho v D}{\mu} = \frac{\rho v (2r)}{\mu}$$

For circular pipes:
- Re < 2300: Laminar (Hagen-Poiseuille valid) ✓
- 2300 < Re < 4000: Transition (unpredictable)
- Re > 4000: Turbulent (Hagen-Poiseuille invalid) ✗

#### Channel volume:

$$V = A \cdot L = \pi r^2 L$$

---

## Solution Method

### Nodal Analysis with Linear Solver

**Step 1: Build Conductance Matrix**

```
For each channel (i -> j) with resistance R_ij:
    Conductance: g_ij = 1 / R_ij
    
    G[i,j] -= g_ij        (off-diagonal: -g)
    G[j,i] -= g_ij        (symmetric: undirected conductance)
    
    G[i,i] += g_ij        (diagonal: sum of connected conductances)
    G[j,j] += g_ij
```

**Step 2: Build Current Vector**

```
I[source] = Q_in        (inject flow)
I[sink] = -Q_in         (extract flow)
I[other] = 0            (no external flow)
```

**Step 3: Apply Boundary Conditions**

```
Set sink pressure to reference:
    G[sink, :] = 0
    G[sink, sink] = 1
    I[sink] = P_ref = 0 Pa
```

**Step 4: Solve Linear System**

$$G \cdot P = I$$

Using sparse linear solver (LU decomposition or GMRES for large systems).

**Step 5: Back-substitute to Find Flows**

For each channel $(i \to j)$:

$$Q_{ij} = \frac{P_i - P_j}{R_h^{ij}}$$

$$\Delta P_{ij} = P_i - P_j$$

---

### Why This Works

The method exploits **linearity:**
- Hagen-Poiseuille law is linear: $\Delta P = R \cdot Q$
- Continuity is linear: $\Sigma Q = 0$
- Result: Linear system with unique solution (if well-posed)

**Contrast with turbulent flow:**
- Drag proportional to $Q^2$ (nonlinear)
- Requires iterative solver (fixed-point or Newton-Raphson)
- Multiple solutions possible
- Numerical complexity higher

---

## Validation Strategy

### Analytical Validation: Series and Parallel

#### Series Configuration

```
Source --[R1]--[R2]--[R3]-- Sink

Analytical: R_total = R1 + R2 + R3
```

**Why it's a good test:**
- Trivial to compute by hand
- Single flow path → flows are equal → easy to verify
- Any error will be obvious

---

#### Parallel Configuration

```
      [R1]
Source <      > Sink
      [R2]

Analytical: 1/R_total = 1/R1 + 1/R2
           R_total = (R1*R2)/(R1+R2)
```

**Why it's a good test:**
- Verifies ability to handle multiple paths
- Checks flow splitting
- Tests pressure balance across parallel branches

---

### Functional Validation: Branching Network

```
        [R1]
0 (src) -----> 1 (junc) -----> 3 (snk)
               |   [R2]   |
               +-> 2 -----+
                   [R4]

Requirements:
  1. Flow conservation at junction
  2. Pressure consistency
  3. No negative flows
  4. Physical bounds respected
```

---

## Implementation Details

### Class Structure

#### `Channel`
- **Attributes:** length, radius, resistance (computed)
- **Methods:** pressure_drop(), velocity(), dissipated_power()
- **Validation:** check_constraints()

#### `Network`
- **Attributes:** nodes, edges (channels), adjacency list
- **Methods:** add_channel(), check_connectivity(), total_volume()
- **Boundary conditions:** source_id, sink_id, Q_in, P_ref

#### `LinearSolver`
- **Input:** Network instance
- **Method:** nodal analysis + linear system solve
- **Output:** pressures[], flows in channels
- **Validation:** validate_solution()

---

### Code Example: Solving a Simple Series Network

```python
from construtal_flow.network import Network
from construtal_flow.solver import LinearSolver

# Create network
net = Network(num_nodes=4, source_id=0, sink_id=3)
net.Q_in = 1.0  # 1 m³/s

# Add three channels
net.add_channel(0, 1, length=1.0, radius=0.05)
net.add_channel(1, 2, length=1.0, radius=0.05)
net.add_channel(2, 3, length=1.0, radius=0.05)

# Solve
solver = LinearSolver(net)
pressures, converged = solver.solve()

# Check
if converged and solver.validate_solution():
    metrics = net.get_network_metrics()
    print(f"R_eff = {metrics['R_eff']:.2e} Pa·s/m³")
    print(f"P_diss = {metrics['P_diss_total']:.2e} W")
```

---

## Error Analysis

### Numerical Errors

1. **Linear System Solver Error**
   - Matrix condition number: $\kappa(G)$
   - Solver tolerance: typically 10⁻¹²
   - Error: < 10⁻¹⁰ (machine precision)

2. **Discretization Error**
   - N/A for Phase 1 (no spatial discretization)
   - Will be relevant in future CFD phases

### Physical Errors (Model Limitations)

1. **Entrance Effects (Ignored)**
   - Hagen-Poiseuille assumes fully developed flow
   - Real entrance region: 0.05 Re·D to 0.1 Re·D
   - Error: ~5% for L/D > 50

2. **Turbulence (Not Handled)**
   - Hagen-Poiseuille valid only for Re < 2300
   - Must check: v_max constraint enforced
   - Error: Infinite if turbulence occurs

3. **Non-Circular Channels (Not Supported)**
   - Hagen-Poiseuille is shape-specific
   - Round pipes have minimum resistance for given area
   - Rectangular, triangular channels would have different R

### Validation Success Criteria

| Test | Criterion | Achieved |
|------|-----------|----------|
| Series (analytical) | Rel error < 1% | ✓ |
| Parallel (analytical) | Rel error < 1% | ✓ |
| Branching (numerical) | Flow error < 10⁻⁶ m³/s | ✓ |
| Pressure balance | Error < 10⁻³ Pa | ✓ |
| Connectivity | Must form path source→sink | ✓ |
| Constraints | All geometric bounds satisfied | ✓ |

---

## Reproducibility Checklist

To reproduce Phase 1 results:

- [ ] Python version ≥ 3.9
- [ ] NumPy, SciPy, Matplotlib installed
- [ ] Run `pytest tests/ -v` to verify
- [ ] Run `python main.py` to execute experiments
- [ ] Compare output plots to reference
- [ ] All experiments should show ✓ PASS

---

## References

### Fundamental Fluid Mechanics

1. White, F. M. (2011). "Fluid Mechanics" (7th ed.). McGraw-Hill.
   - Chapter 6: Viscous Flow in Ducts

2. Schlichting, H., & Gersten, K. (2016). "Boundary-Layer Theory" (9th ed.). Springer.
   - Section 4.2: Laminar flow in pipes

### Network Analysis

3. Newman, M. E. J. (2018). "Networks" (2nd ed.). Oxford University Press.
   - Chapter 2: Basics of networks

4. Doyle, P. G., & Snell, J. L. (1984). "Random Walks and Electric Networks."
   - Classic reference on electrical-hydraulic analogy

### Constructal Theory

5. Bejan, A. (2000). "Shape and Structure, from Engineering to Nature." Cambridge University Press.

6. Bejan, A., & Zane, J. P. (2012). "Design in Nature." Dover.

---

## Glossary

| Term | Symbol | Unit | Meaning |
|------|--------|------|---------|
| Volumetric flow rate | Q | m³/s | Volume of fluid per unit time |
| Pressure | P | Pa (N/m²) | Force per unit area |
| Pressure drop | ΔP | Pa | P_upstream - P_downstream |
| Hydraulic resistance | R_h | Pa·s/m³ | Resistance to flow (analogy to electrical R) |
| Dynamic viscosity | μ | Pa·s | Fluid's resistance to shear |
| Channel length | L | m | Physical length of pipe |
| Channel radius | r | m | Internal radius of pipe |
| Velocity | v | m/s | Speed of fluid motion |
| Reynolds number | Re | (dimensionless) | Ratio of inertial to viscous forces |
| Effective resistance | R_eff | Pa·s/m³ | Total network resistance from source to sink |
| Dissipated power | P_diss | W | Energy converted to heat per unit time |
| Entropy generation | Ṡ_gen | W/K | Rate of irreversibility |

---

## Future Refinements (Phase 2+)

- [ ] Geometric optimization (channel radii tuning)
- [ ] Topological optimization (add/remove channels)
- [ ] Thermal coupling (heat transfer + flow)
- [ ] Nonlinear optimization (gradient-based)
- [ ] Visualization (network diagrams, flow animations)
- [ ] Constructal heuristics (automatic architecture evolution)
- [ ] Multi-objective optimization (Pareto frontiers)

---

**Document Version:** 1.0  
**Last Updated:** 2026-09-10  
**Author:** Enio Carlos
