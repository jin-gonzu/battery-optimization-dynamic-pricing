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
| $E^B_i$ | Bonus for remaining charge at end of step $i$ | $E^B_i \in [-\infty,\infty]$ |
| **Binary Control Variables** | | |
| $d_i$ | 1 if discharge allowed at step $i$ | $\{0,1\}$ |
| $c_i$ | 1 if charging at step $i$ | $\{0,1\}$ |
| $x_i$ | 1 if discharging at step $i$ | $\{0,1\}$ |
| $m_i$ | 1 if energy import at step $i$ | $\{0,1\}$ |
| $y_i$ | 1 if energy export at step $i$ | $\{0,1\}$ |

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

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/Battery-Optimization-With-Dynamic-Energy-Pricing.git
cd Battery-Optimization-With-Dynamic-Energy-Pricing
python -m pip install ortools

https://developers.google.com/optimization/install?hl=de

