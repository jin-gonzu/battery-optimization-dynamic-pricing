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

---

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

$$
B_{i+1} = B_i + E^C_i - E^D_i, \quad \forall i \in I
$$

$$
B_{c,\min} \le B_i \le B_{c,\max}, \quad \forall i \in I
$$

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/Battery-Optimization-With-Dynamic-Energy-Pricing.git
cd Battery-Optimization-With-Dynamic-Energy-Pricing
python -m pip install ortools

https://developers.google.com/optimization/install?hl=de

