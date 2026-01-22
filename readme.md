# Battery Optimization with Dynamic Energy Pricing

This project implements an optimization model for battery charging and discharging using dynamic electricity prices.  
It schedules battery usage to minimize energy costs, can avoid switching, and respect battery constraints.

## Symbol Definitions

| Symbol | Description | Range |
|--------|-------------|-------|
| $I$ | Discrete time interval | $i \in \{0,\ldots,I_{\max}\}$ |
| $C_i$ | Energy consumption at time $i \in I$ | $C_i \in [0,\infty)$ |
| $P_i$ | Energy price at time $i \in I$ | $P_i \in [0,\infty)$ |
| $P_{\mathrm{solar}}$ | Price for selling solar power | $P_{\mathrm{solar}} \in [0,\infty)$ |
| $S_i$ | Solar energy produced at time $i \in I$ | $S_i \in [0,\infty)$ |
| **Battery Parameters** | | |
| $B_{c,\max}$ | Maximum capacity of battery | $B_{c,\max} \in [B_{c,\min},\infty)$ |
| $B_{c,\min}$ | Minimum capacity of battery | $B_{c,\min} \in [0,B_{c,\max}]$ |
| $B_{c,\mathrm{initial}}$ | Initial capacity of battery | $B_{c,\mathrm{initial}} \in [B_{c,\min},B_{c,\max}]$ |
| $B_\text{charge}^{\max}$ | Maximum charge of battery in one interval | $B_\text{charge}^{\max} \in [0,B_{c,\max}]$ |
| $B_\text{discharge}^{\max}$ | Maximum discharge of battery in one interval | $B_\text{discharge}^{\max} \in [0,B_{c,\max}]$ |
| $P_{\mathrm{loaded}}$ | Price for which the battery was loaded | $P_{\mathrm{loaded}} \in [0,B_{c,\max}]$ |

## Energy Model Variables

| Symbol | Description | Range |
|--------|-------------|-------|
| **Battery Variables** | | |
| $B_i$ | Battery state at step $i$ | $B_i \in [B_{c,\min},B_{c,\max}]$ |
| $E^C_i$ | Energy charged to battery at step $i$ | $E^C_i \in [0,B_\text{charge}^{\max}]$ |
| $E^D_i$ | Energy discharged from battery at step $i$ | $E^D_i \in [0,B_\text{discharge}^{\max}]$ |
| **Energy Flow Variables** | | |
| $E^G_i$ | Energy bought from the grid at step $i$ | $E^G_i \in [0,\infty)$ |
| $E^{GL}_i$ | Energy from grid to load at step $i$ | $E^{OL}_i \in [0,\infty)$ |
| $E^{GB}_i$ | Energy from grid to battery at step $i$ | $E^{GB}_i \in [0,B_\text{charge}^{\max}]$ |
| $E^{SB}_i$ | Solar energy charged to battery at step $i$ | $E^{SB}_i \in [0,B_\text{charge}^{\max}]$ |
| $E^{SL}_i$ | Solar energy to load at step $i$ | $E^{SL}_i \in [0,S_i]$ |
| $E^S_i$ | Solar energy sold at step $i$ | $E^S_i \in [0,S_i]$ |
| **Initial Energy Variables** | | |
| $E^U_i$ | Used initial energy at step $i$ | $E^U_i \in [0,B_{c,\mathrm{initial}}]$ |
| $E^0_i$ | Remaining initial energy at step $i$ | $E^0_i \in [0,B_{c,\mathrm{initial}}]$ |
| $E^B$ | Bonus for remaining charge at the last step | $E^B \in [-\infty,\infty]$ |
| **Binary Control Variables** | | |
| $d_i$ | 1 if discharge allowed at step $i$ | $\{0,1\}$ |
| $c_i$ | 1 if charging at step $i$ | $\{0,1\}$ |
| $x_i$ | 1 if discharging at step $i$ | $\{0,1\}$ |
| $m_i$ | 1 if energy import at step $i$ | $\{0,1\}$ |
| $y_i$ | 1 if energy export at step $i$ | $\{0,1\}$ |

## Mathematical Model Formulation

### 1. Objective Function
**Minimize total cost:**

$$
\min \quad \sum_{i \in I} \left( P_i \cdot E^G_i - P_{\mathrm{solar}} \cdot E^S_i \right) - P_{\mathrm{loaded}} \cdot B_{c,\mathrm{initial}} + P_{\mathrm{loaded}} \cdot B_{I_{\max}}
$$

### 2. Energy Balance Constraints
**Load energy balance:**

$$
C_i = E^{SL}_i + E^D_i + E^{GL}_i, \quad \forall i \in I
$$

**Solar energy balance:**

$$
S_i = E^{SB}_i + E^{SL}_i + E^S_i, \quad \forall i \in I
$$

**Grid energy decomposition:**

$$
E^G_i = E^{GB}_i + E^{GL}_i, \quad \forall i \in I
$$

### 3. Battery State Dynamics
**Initial battery state:**

$$
B_0 = B_{c,\mathrm{initial}} + E^C_0 - E^D_0
$$

**Battery state evolution:**

$$
B_i = B_{i-1} + E^C_i - E^D_i, \quad \forall i \in I \setminus \{0\}
$$

### 4. Battery Charging and Discharging Constraints
**Battery charging limit:**

$$
E^C_i \le B_\text{charge}^{\max} \cdot c_i, \quad \forall i \in I
$$

**Battery discharging limit:**

$$
E^D_i \le B_\text{discharge}^{\max} \cdot x_i, \quad \forall i \in I
$$

**Total battery charging:**

$$
E^C_i = E^{SB}_i \cdot 0.9 + E^{GB}_i, \quad \forall i \in I
$$

**Grid-to-battery minimum flow:**

$$
E^{GB}_i \ge B_\text{charge}^{\max} \cdot c_i - E^{SB}_i \cdot 0.9, \quad \forall i \in I
$$

### 5. Binary Control Constraints
**No simultaneous charging and discharging:**

$$
c_i + x_i \le 1, \quad \forall i \in I
$$

**No simultaneous import and export:**

$$
m_i + y_i \le 1, \quad \forall i \in I
$$

**Grid import control (Big-M constraint):**

$$
E^{GL}_i + E^{GB}_i \le M \cdot m_i, \quad \forall i \in I
$$

**Solar export control (Big-M constraint):**

$$
E^S_i \le M \cdot y_i, \quad \forall i \in I
$$

**Binary variable definitions:**

$$
c_i, x_i, m_i, y_i \in \{0,1\}, \quad \forall i \in I
$$

### 6. Initial Energy Tracking
**Initial energy at start:**

$$
E^0_0 = B_{c,\mathrm{initial}}
$$

**Remaining initial energy bounded by battery state:**

$$
E^0_i \le B_i, \quad \forall i \in I
$$

**Remaining initial energy definition:**

$$
E^0_i \ge B_{c,\mathrm{initial}} - \sum_{j=0}^{i} E^D_j, \quad \forall i \in I
$$

**Used initial energy at each step:**

$$
E^U_i = B_{c,\mathrm{initial}} - E^0_i, \quad \forall i \in I
$$

### 7. End-of-Period Accounting
**Bonus for remaining charge at end:**

$$
E^B = B_{I_{\max}} - E^0_{I_{\max}}
$$

## Project Structure

- `solver.py` – OR-Tools solver using `pywraplp.Solver.CreateSolver("CBC")` or `"SCIP"`  
- `Solar.py` – Main script to run the optimization  
- `example.py` – Example dataset and usage for testing

---

## Features

- Smart battery scheduling based on dynamic energy prices
- Minimize electricity costs
- Consider battery constraints:
  - Capacity limits
  - Charge/discharge power limits
- Can penalize frequent on/off switching
- Support for PV generation
- Built using Google OR-Tools

---

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/Battery-Optimization-With-Dynamic-Energy-Pricing.git
cd Battery-Optimization-With-Dynamic-Energy-Pricing
python -m pip install ortools

https://developers.google.com/optimization/install?hl=de

