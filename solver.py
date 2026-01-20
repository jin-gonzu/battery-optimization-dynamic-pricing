from ortools.linear_solver import pywraplp

def create_vars(s, I, mc, md, bs_min, bs_max, init_bs):
    return (
        {i: s.IntVar(0, s.infinity(), f"oP_{i}") for i in I},
        {i: s.IntVar(0, mc, f"bC_{i}") for i in I},
        {i: s.IntVar(0, md, f"bD_{i}") for i in I},
        {i: s.IntVar(bs_min, bs_max - 1000, f"bS_{i}") for i in I},
        {i: s.IntVar(0, s.infinity(), f"sell_{i}") for i in I},
        {i: s.IntVar(0, s.infinity(), f"s2b_{i}") for i in I},
        {i: s.IntVar(0, 1, f"dA_{i}") for i in I},
        {i: s.NumVar(0, init_bs, f"initE_{i}") for i in I},
        {i: s.IntVar(0, 1, f"isCharging_{i}") for i in I},
    )

def solve_solar(interval,
                consumption,
                price_outside_power,
                price_selling_energy,
                solar_production,
                battery_initial_capacity,
                battery_minimal_capacity,
                battery_charge_power,
                battery_discharge_power,
                battery_max_capacity, 
                price_using_battery,
                battery_target_capacity,
                mustLoadFirst, min_battery_discharge,
                printEnabled):
    
    solver = pywraplp.Solver.CreateSolver("CBC")  # oder "SCIP"

    if not solver:
        raise RuntimeError("Solver konnte nicht erstellt werden")
       
    #create variables
    (outside_power, battery_charge, battery_discharge, battery_status, selling, solar_to_battery, dischargeAllowed
     , initial_energy_left, is_charging) = create_vars( solver, interval, battery_charge_power, battery_discharge_power, battery_minimal_capacity, battery_max_capacity, battery_initial_capacity )

    #discharge and charge cannot happen at the same time
    for i in interval:
        solver.Add(battery_charge[i] <= battery_charge_power * is_charging[i])
        solver.Add(solar_to_battery[i] <= battery_charge_power * is_charging[i])
        solver.Add(battery_discharge[i] <= battery_discharge_power * (1 - is_charging[i]))    
    
    #constraint for bool variable dischargeAllowed
    # in case the battery was at under 30 % the inverter will first load the battery to 80 % before allowing the battery to discharge
    if(mustLoadFirst):
        for i in interval:
            if(i == 0):
                #initially the variable is based on the initial battery status
                solver.Add( dischargeAllowed[i] <= (battery_status[i] / min_battery_discharge))
            else:
                # in case the 
                solver.Add(dischargeAllowed[i] <= (battery_status[i] / min_battery_discharge) + dischargeAllowed[i-1])
            solver.Add(battery_discharge[i] >= -battery_discharge_power * dischargeAllowed[i])
            solver.Add(battery_charge[i] <= battery_charge_power)

    #calculation of battery status, history, start and end
    solver.Add(battery_status[0] == battery_initial_capacity + battery_charge[0] - battery_discharge[0] + solar_to_battery[0])
    solver.Add(battery_status[interval[-1]] == battery_target_capacity)
    for i in range(1, len(interval)):
        solver.Add(battery_status[i] == battery_status[i-1] + battery_charge[i] - battery_discharge[i] + solar_to_battery[i])

    #initialEnergyLeft
    #solver.Add(initial_energy_left[0] == battery_initial_capacity)
    #for i in interval:
    #    solver.Add(initial_energy_left[i] <= battery_status[i])
    #    
    #for i in interval:
    #    solver.Add(
    #        initial_energy_left[i]
    #        >= battery_initial_capacity
    #        - sum(battery_discharge[j] for j in interval if j <= i)
    #    )
    
    for i in interval:
        solver.Add(
            solar_production[i]
            + outside_power[i]
            - battery_charge[i] + battery_discharge[i]
            - solar_to_battery[i]
            == consumption[i] + selling[i]
        )
        
    for i in interval:
        solver.Add(selling[i] <= solar_production[i] - solar_to_battery[i])
        solver.Add(solar_to_battery[i] <= solar_production[i]  * 0.9 - selling[i])
    
    
    switch = {}
    for i in interval[1:]:
        switch[i] = solver.BoolVar(f"switch_{i}")

    for i in interval[1:]:
        solver.Add(switch[i] >= is_charging[i] - is_charging[i-1])
        solver.Add(switch[i] >= is_charging[i-1] - is_charging[i])

    objective = solver.Objective()
    for i in interval:
        objective.SetCoefficient(outside_power[i], price_outside_power[i])
        objective.SetCoefficient(selling[i], -price_selling_energy)
        if(i > 0):
            objective.SetCoefficient(switch[i], 5000000)
        #objective.SetCoefficient(initial_energy_left[interval[-1]],price_using_battery)

    objective.SetMinimization()

    status = solver.Solve()

    soc_list = []
    energy_bought_list = []
    battery_discharge_list = []
    battery_charge_list = []
    solar_energy_list = []

    if status != pywraplp.Solver.OPTIMAL:
        print("Keine optimale Lösung gefunden")
        return soc_list, energy_bought_list, battery_discharge_list,battery_charge_list, solar_energy_list

    print("Der optimierte Strompreis liegt bei: ", objective.Value() / 1000 / 100)
    print()

    # Header mit Tabs
    print(
        f"Step\tUsed\tOutside\tKosten\tSolar\tSold\tSOC(%)\tBC\tBDC\tSolar\tinitial\tBS"
    )

    costs_without_balancing = 0
    costs_with_balancing = 0
    energy_bought = 0
    for i in interval:
        soc_percent = (battery_status[i].solution_value() / battery_max_capacity) * 100  # SOC in %
        soc_list.append(soc_percent)
        
        costs_without_balancing += consumption[i] * price_outside_power[i]
        costs_with_balancing += outside_power[i].solution_value() * price_outside_power[i]
        energy_bought +=outside_power[i].solution_value()
        
        energy_bought_list.append(outside_power[i].solution_value())
        battery_discharge_list.append(battery_discharge[i].solution_value())
        battery_charge_list.append(battery_charge[i].solution_value())
        solar_energy_list.append(solar_production[i])
        
        if(printEnabled):
            print(
                f"{i}\t"
                f"{consumption[i]}\t"
                f"{outside_power[i].solution_value()}\t"
                f"{price_outside_power[i]}\t"
                f"{solar_production[i]}\t"
                f"{selling[i].solution_value()}\t"
                f"{soc_percent:.1f}\t"  # SOC in %
                f"{battery_charge[i].solution_value()}\t"
                f"{battery_discharge[i].solution_value()}\t"
                f"{solar_to_battery[i].solution_value()}\t"
                f"{dischargeAllowed[i].solution_value()}\t"
                f"{initial_energy_left[i].solution_value():.1f}\t"
                f"{battery_status[i].solution_value():.1f}"
            )

    return soc_list, energy_bought_list, battery_discharge_list,battery_charge_list, solar_energy_list