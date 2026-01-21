from ortools.linear_solver import pywraplp

def create_vars(s, I, mc, md, bs_min, bs_max, init_bs):
    return (
        {i: s.IntVar(0, s.infinity(), f"oP_{i}") for i in I},
        {i: s.IntVar(0, mc, f"bC_{i}") for i in I},
        {i: s.IntVar(0, md, f"bD_{i}") for i in I},
        {i: s.IntVar(bs_min, bs_max, f"bS_{i}") for i in I},
        {i: s.IntVar(0, s.infinity(), f"sell_{i}") for i in I},
        {i: s.IntVar(0, md, f"solar_to_battery_{i}") for i in I},
        {i: s.BoolVar(f"dA_{i}") for i in I},
        {i: s.IntVar(0, init_bs, f"initE_{i}") for i in I},
        {i: s.BoolVar(f"isCharging_{i}") for i in I},
        {i: s.BoolVar(f"isDisCharging_{i}") for i in I},
    )

def addConstraintDisCharge(solver, interval, battery_discharge, battery_discharge_power, is_discharging):
    for i in interval:
        solver.Add(battery_discharge[i] <= battery_discharge_power * is_discharging[i])

def addConstraintBatteryStatus(solver, interval, battery_status, battery_charge, battery_discharge, solar_to_battery, battery_initial_capacity ):
    #calculation of battery status, history, start and end
    solver.Add(battery_status[0] == battery_initial_capacity + battery_charge[0] - battery_discharge[0])
    
    #solver.Add(battery_status[interval[-1]] == battery_initial_capacity)

    for i in range(1, len(interval)):
        solver.Add(battery_status[i] == battery_status[i-1] + battery_charge[i] - battery_discharge[i])

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
     , initial_energy_left, is_charging, is_discharging) = create_vars( solver, interval, battery_charge_power, battery_discharge_power, battery_minimal_capacity, battery_max_capacity, battery_initial_capacity )

    outside_to_battery = {}
    outside_to_load = {}
    solar_to_load = {}
    is_import = {}
    is_export = {}
    M = 10000

    for i in interval:
        outside_to_battery[i] = solver.IntVar(0, battery_charge_power, f"otB_{i}")
        outside_to_load[i] = solver.IntVar(0, solver.infinity(), f"otG_{i}")
        solar_to_load[i] = solver.IntVar(0, solver.infinity(), f"stG_{i}")
        is_import[i] = solver.BoolVar(f"is_import_{i}")
        is_export[i] = solver.BoolVar(f"is_export_{i}")
    
    for i in interval:
            #set the variable is_charging
            # it must be 1 in case the battery_status goes up
            # and it must be 0 in case the battery does not change or discharge is happening
                #solver.Add(battery_status[i] >= battery_status[i-1] + delta - battery_max_capacity * (1 - is_charging[i]))
                #solver.Add(battery_status[i] <= battery_status[i-1] + battery_max_capacity * is_charging[i])
            #set the variable is_discharging
            # it must be 1 in case the battery_status goes down
            # and it must be 0 in case the battery does not change or charge is happening
                #solver.Add(battery_status[i] <= battery_status[i-1] - delta + battery_max_capacity * (1 - is_discharging[i]))
                #solver.Add(battery_status[i] >= battery_status[i-1] - battery_max_capacity * is_discharging[i])

            solver.Add(is_charging[i] + is_discharging[i] <= 1)
            
            solver.Add(outside_to_load[i] + outside_to_battery[i] <= M * is_import[i])
            solver.Add(selling[i] <= M * is_export[i])
            solver.Add(is_import[i] + is_export[i] <= 1)


    for i in interval:
        solver.Add(battery_charge[i] <= battery_charge_power * is_charging[i])
        solver.Add(outside_power[i] == outside_to_battery[i] + outside_to_load[i])
        solver.Add(outside_to_battery[i] >= battery_charge_power * is_charging[i] - solar_to_battery[i]*0.9)
        solver.Add(battery_charge[i] == solar_to_battery[i] * 0.9 + outside_to_battery[i])


    addConstraintDisCharge(solver, interval, battery_discharge, battery_discharge_power, is_discharging)

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

    # battery status constraints, history of battery status and fill level
    addConstraintBatteryStatus(solver, interval, battery_status, battery_charge, battery_discharge, solar_to_battery, battery_initial_capacity )



    #initialEnergyLeft
    solver.Add(initial_energy_left[0] == battery_initial_capacity)
    for i in interval:
        solver.Add(initial_energy_left[i] <= battery_status[i])
        
    for i in interval:
        solver.Add(
            initial_energy_left[i]
            >= battery_initial_capacity
            - sum(battery_discharge[j] for j in interval if j <= i)
        )
    

    for i in interval:
        solver.Add(consumption[i] == solar_to_load[i] + battery_discharge[i] + outside_to_load[i] )
        solver.Add(solar_production[i] == solar_to_battery[i] + solar_to_load[i] + selling[i])
    
    #if one would want to disable switching
    #switch = {}
    #for i in interval[1:]:
    #    switch[i] = solver.BoolVar(f"switch_{i}")
    #
    #for i in interval[1:]:
    #    solver.Add(switch[i] >= is_charging[i] - is_charging[i-1])
    #    solver.Add(switch[i] >= is_charging[i-1] - is_charging[i])

    end_charge_bonus = solver.NumVar(-solver.infinity(), solver.infinity(), "end_charge_bonus")
    solver.Add(end_charge_bonus == battery_status[interval[-1]] - initial_energy_left[interval[-1]] - battery_status[interval[0]])
    used_initial_energy = {}
    
    for i in interval:
        used_initial_energy[i] = solver.NumVar(0, battery_initial_capacity, f"used_initial_energy[{i}]")
        solver.Add(used_initial_energy[i] == battery_initial_capacity - initial_energy_left[i])
        
    objective = solver.Objective()
    for i in interval:
        #the loaded energy has a price, if the inital enery was used, it must be payed
        objective.SetCoefficient(used_initial_energy[i], price_using_battery)
        #the left over inside the battery is something positiv, we still have this value
        objective.SetCoefficient(initial_energy_left[interval[-1]], -price_using_battery)

        # we must pay all the energy we bought from outside
        objective.SetCoefficient(outside_power[i], price_outside_power[i])

        #we get the money from selling energy
        objective.SetCoefficient(selling[i], -price_selling_energy)

        #if we load more inside the battery, we create value
        objective.SetCoefficient(end_charge_bonus, -price_selling_energy)
        #if(i > 0):
        #    objective.SetCoefficient(switch[i], 5000000)



    objective.SetMinimization()

    status = solver.Solve()

    soc_list = []
    energy_bought_list = []
    battery_discharge_list = []
    battery_charge_list = []
    solar_energy_list = []
    is_charging_list = []
    is_discharging_list = []
    outside_to_battery_list = []
    solar_to_battery_list = []

    if status != pywraplp.Solver.OPTIMAL:
        print("Keine optimale Lösung gefunden")
        return soc_list, energy_bought_list, battery_discharge_list,battery_charge_list, solar_energy_list,is_charging_list, is_discharging_list, outside_to_battery_list,solar_to_battery_list

    # Header mit Tabs
    print(
        f"Step\tUsed\tOutside\tKosten\tSolar\tSold\tSOC(%)\tBC\tisChar\tisDChar\tBDC\tSolTB\tOuTB\tinitial\tBS"
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
        is_charging_list.append(is_charging[i].solution_value())
        is_discharging_list.append(is_discharging[i].solution_value())
        outside_to_battery_list.append(outside_to_battery[i].solution_value())
        solar_to_battery_list.append(solar_to_battery[i].solution_value())

        if(battery_discharge[i].solution_value() > battery_discharge_power):
            print("Error Discharge Value too hight")

        if(selling[i].solution_value() > 0 and outside_power[i].solution_value() > 0):
            print("Error Selling and Buying is impossible at the same time")
            print(f" Charge: {battery_charge[i].solution_value()}, davon Solar: {round(solar_to_battery[i].solution_value())} also *0.9: {round(solar_to_battery[i].solution_value()) *0.9} und davon Grid {round(outside_to_battery[i].solution_value())} ")
            print(f" Consum: {consumption[i]}, davon Solar: {round(solar_to_load[i].solution_value())} und davon Grid {round(outside_to_load[i].solution_value())} ")
            print(f" Verfügbarer Solarstrom: {solar_production[i]}, davon verkauft: {selling[i].solution_value()}")
            print(f" Import?: {is_import[i].solution_value()}, Export?: {is_export[i].solution_value()}")

            

        if(is_charging[i].solution_value() == 0 and ( round(solar_to_battery[i].solution_value()) > 0 or round(outside_to_battery[i].solution_value()) > 0) ):
            print("Error is Charging must be set, if loading occures")

        if(is_charging[i].solution_value() == 1 and is_discharging[i].solution_value() == 1 ):
            print("Error is Charging and is Discharging must never be 1 at the same time")


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
                f"{is_charging[i].solution_value()}\t"
                f"{is_discharging[i].solution_value()}\t"
                f"{battery_discharge[i].solution_value()}\t"
                f"{round(solar_to_battery[i].solution_value())}\t"
                f"{round(outside_to_battery[i].solution_value())}\t"
                f"{initial_energy_left[i].solution_value():.1f}\t"
                f"{battery_status[i].solution_value():.1f}"
            )

    return soc_list, energy_bought_list, battery_discharge_list,battery_charge_list, solar_energy_list,is_charging_list, is_discharging_list, outside_to_battery_list,solar_to_battery_list