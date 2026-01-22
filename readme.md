# Battery Optimization with Dynamic Energy Pricing

This project implements an optimization model for battery charging and discharging using dynamic electricity prices.  
It schedules battery usage to minimize energy costs, can avoid switching, and respect battery constraints.

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

$\sum_{i \in I}$
