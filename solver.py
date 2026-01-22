from ortools.linear_solver import pywraplp


def addConstraintDisCharge(solver, interval, E_D, B_discharge_max, x):
    for i in interval:
        solver.Add(E_D[i] <= B_discharge_max * x[i])

def addConstraintBatteryStatus(solver, interval, B, E_C, E_D, E_SB, B_c_initial ):
    #calculation of battery status, history, start and end
    solver.Add(B[0] == B_c_initial + E_C[0] - E_D[0])
    
    #solver.Add(B[interval[-1]] == B_c_initial)

    for i in range(1, len(interval)):
        solver.Add(B[i] == B[i-1] + E_C[i] - E_D[i])

def solve_solar(interval,
                C,
                P,
                P_solar,
                S,
                B_c_initial,
                B_c_min,
                B_charge_max,
                B_discharge_max,
                B_c_max, 
                P_loaded,
                battery_target_capacity,
                mustLoadFirst, min_battery_discharge,
                printEnabled):
    
    solver = pywraplp.Solver.CreateSolver("CBC")  # oder "SCIP"

    if not solver:
        raise RuntimeError("Solver konnte nicht erstellt werden")
       
    #-----------------------Battery Variables
    B     = {i: solver.IntVar(B_c_min, B_c_max,       f"B_{i}")          for i in interval}
    E_C   = {i: solver.IntVar(0, B_charge_max,        f"E_C_{i}")        for i in interval}
    E_D   = {i: solver.IntVar(0, B_discharge_max,     f"E_D_{i}")        for i in interval}

    #-----------------------Energy Flow Variables
    E_G   = {i: solver.IntVar(0, solver.infinity(),   f"E_G_{i}")        for i in interval}
    E_GL  = {i: solver.IntVar(0, solver.infinity(),   f"E_GL_{i}")       for i in interval}
    E_GB  = {i: solver.IntVar(0, B_charge_max,        f"E_GB_{i}")       for i in interval}
    
    E_SB  = {i: solver.IntVar(0, B_discharge_max,     f"E_SB_{i}")       for i in interval}
    E_SL  = {i: solver.IntVar(0, solver.infinity(),   f"E_SL_{i}")       for i in interval}
    E_S   = {i: solver.IntVar(0, solver.infinity(),   f"E_S_{i}")        for i in interval}

    #---------------------Initial Energy Variables
    E_0   = {i: solver.IntVar(0, B_c_initial,         f"E_0_{i}")        for i in interval}
    E_U   = {i: solver.IntVar(0, B_c_initial,         f"E_U_{i}")        for i in interval}
    E_B   = solver.IntVar(-solver.infinity(), solver.infinity(), "E_B")
    
    #---------------------Binary Control Variables
    d     = {i: solver.BoolVar(f"d_{i}")                             for i in interval}
    c     = {i: solver.BoolVar(f"c_{i}")                             for i in interval}
    x     = {i: solver.BoolVar(f"x_{i}")                             for i in interval}
    m     = {i: solver.BoolVar(f"m_{i}")                             for i in interval}
    y     = {i: solver.BoolVar(f"y_{i}")                             for i in interval}

    M = 10000
    
    for i in interval:
            #set the variable c
            # it must be 1 in case the B goes up
            # and it must be 0 in case the battery does not change or discharge is happening
                #solver.Add(B[i] >= B[i-1] + delta - B_c_max * (1 - c[i]))
                #solver.Add(B[i] <= B[i-1] + B_c_max * c[i])
            #set the variable x
            # it must be 1 in case the B goes down
            # and it must be 0 in case the battery does not change or charge is happening
                #solver.Add(B[i] <= B[i-1] - delta + B_c_max * (1 - x[i]))
                #solver.Add(B[i] >= B[i-1] - B_c_max * x[i])

            solver.Add(c[i] + x[i] <= 1)
            
            solver.Add(E_GL[i] + E_GB[i] <= M * m[i])
            solver.Add(E_S[i] <= M * y[i])
            solver.Add(m[i] + y[i] <= 1)


    for i in interval:
        solver.Add(E_C[i] <= B_charge_max * c[i])
        solver.Add(E_G[i] == E_GB[i] + E_GL[i])
        solver.Add(E_GB[i] >= B_charge_max * c[i] - E_SB[i]*0.9)
        solver.Add(E_C[i] == E_SB[i] * 0.9 + E_GB[i])


    addConstraintDisCharge(solver, interval, E_D, B_discharge_max, x)

    #constraint for bool variable d
    # in case the battery was at under 30 % the inverter will first load the battery to 80 % before allowing the battery to discharge
    if(mustLoadFirst):
        for i in interval:
            if(i == 0):
                #initially the variable is based on the initial battery status
                solver.Add( d[i] <= (B[i] / min_battery_discharge))
            else:
                # in case the 
                solver.Add(d[i] <= (B[i] / min_battery_discharge) + d[i-1])
            solver.Add(E_D[i] >= -B_discharge_max * d[i])
            solver.Add(E_C[i] <= B_charge_max)

    # battery status constraints, history of battery status and fill level
    addConstraintBatteryStatus(solver, interval, B, E_C, E_D, E_SB, B_c_initial )



    #initialEnergyLeft
    solver.Add(E_0[0] == B_c_initial)
    for i in interval:
        solver.Add(E_0[i] <= B[i])
        
    for i in interval:
        solver.Add(
            E_0[i]
            >= B_c_initial
            - sum(E_D[j] for j in interval if j <= i)
        )
    

    for i in interval:
        solver.Add(C[i] == E_SL[i] + E_D[i] + E_GL[i] )
        solver.Add(S[i] == E_SB[i] + E_SL[i] + E_S[i])
    
    #if one would want to disable switching
    #switch = {}
    #for i in interval[1:]:
    #    switch[i] = solver.BoolVar(f"switch_{i}")
    #
    #for i in interval[1:]:
    #    solver.Add(switch[i] >= c[i] - c[i-1])
    #    solver.Add(switch[i] >= c[i-1] - c[i])

    
    solver.Add(E_B == B[interval[-1]] - E_0[interval[-1]])
    
    for i in interval:
        
        solver.Add(E_U[i] == B_c_initial - E_0[i])
        
    objective = solver.Objective()
    min_price = min(P.values())
    avg_price = sum(P.values()) / len(P)


    battery_objective_new = False
    for i in interval:

        # we must pay all the energy we bought from outside
        objective.SetCoefficient(E_G[i], P[i])
        #we get the money from E_S energy
        objective.SetCoefficient(E_S[i], -P_solar)

        if(battery_objective_new):
            #objective function for the battery and whats inside
                #the loaded energy has a price, if the inital enery was used, it must be payed
            objective.SetCoefficient(E_U[i], P_loaded - P[i])
                #the left over inside the battery is something positiv, we still have this value
            objective.SetCoefficient(E_0[interval[-1]], -P_loaded)
                #if we load more inside the battery, we create value
            objective.SetCoefficient(E_B, -avg_price)
        else:
            #the initial energy is something we have
            objective.SetCoefficient(E_0[0], -P_loaded)
            objective.SetCoefficient(B[interval[-1]], P_loaded)


            #could be used to price the intial start energy
        #objective.SetCoefficient(E_0[0], -P_loaded)

        #if we load more inside the battery, we create value
        #objective.SetCoefficient(B[interval[-1]], -P_loaded)

        #reduce over all outside power
        #objective.SetCoefficient(E_G[i],2000)

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
    elif status == pywraplp.Solver.FEASIBLE:
        print("Zulässige (aber evtl. nicht optimale) Lösung gefunden")

    print("Zielfunktionswert =", solver.Objective().Value())
    

    # Header mit Tabs
    print(
        f"Step\tUsed\tOutside\tKosten\tSolar\tSold\tSOC(%)\tBC\tBDC\tSolTB\tOuTB\tinitial\tBS"
    )

    costs_without_balancing = 0
    costs_with_balancing = 0
    costs_initial_energy = 0
    energy_bought = 0
    for i in interval:
        soc_percent = (B[i].solution_value() / B_c_max) * 100  # SOC in %
        soc_list.append(soc_percent)
        
        costs_without_balancing += C[i] * P[i]
        costs_with_balancing += E_G[i].solution_value() * P[i]
        costs_initial_energy += E_U[i].solution_value() * P_loaded
        energy_bought +=E_G[i].solution_value()
        
        energy_bought_list.append(E_G[i].solution_value())
        battery_discharge_list.append(E_D[i].solution_value())
        battery_charge_list.append(E_C[i].solution_value())
        solar_energy_list.append(S[i])
        is_charging_list.append(c[i].solution_value())
        is_discharging_list.append(x[i].solution_value())
        outside_to_battery_list.append(E_GB[i].solution_value())
        solar_to_battery_list.append(E_SB[i].solution_value())

        if(E_D[i].solution_value() > B_discharge_max):
            print("Error Discharge Value too hight")

        if(E_S[i].solution_value() > 0 and E_G[i].solution_value() > 0):
            print("Error E_S and Buying is impossible at the same time")
            print(f" Charge: {E_C[i].solution_value()}, davon Solar: {round(E_SB[i].solution_value())} also *0.9: {round(E_SB[i].solution_value()) *0.9} und davon Grid {round(E_GB[i].solution_value())} ")
            print(f" Consum: {C[i]}, davon Solar: {round(E_SL[i].solution_value())} und davon Grid {round(E_GL[i].solution_value())} ")
            print(f" Verfügbarer Solarstrom: {S[i]}, davon verkauft: {E_S[i].solution_value()}")
            print(f" Import?: {m[i].solution_value()}, Export?: {y[i].solution_value()}")

            

        if(c[i].solution_value() == 0 and ( round(E_SB[i].solution_value()) > 0 or round(E_GB[i].solution_value()) > 0) ):
            print("Error is Charging must be set, if loading occures")

        if(c[i].solution_value() == 1 and x[i].solution_value() == 1 ):
            print("Error is Charging and is Discharging must never be 1 at the same time")


        if(printEnabled):
            print(
                f"{i}\t"
                f"{C[i]}\t"
                f"{E_G[i].solution_value()}\t"
                f"{P[i]}\t"
                f"{S[i]}\t"
                f"{E_S[i].solution_value()}\t"
                f"{soc_percent:.1f}\t"  # SOC in %
                f"{E_C[i].solution_value()}\t"
                #f"{c[i].solution_value()}\t"
                #f"{x[i].solution_value()}\t"
                f"{E_D[i].solution_value()}\t"
                f"{round(E_SB[i].solution_value())}\t"
                f"{round(E_GB[i].solution_value())}\t"
                #f"{round(E_SL[i].solution_value())}\t"
                #f"{round(E_GL[i].solution_value())}\t"
                f"{E_0[i].solution_value():.1f}\t"
                f"{B[i].solution_value():.1f}"
            )


    print(f"Kosten Einkauf: {costs_with_balancing}, Kosten entladener Initial-Strom: {costs_initial_energy}, Gewinn durch nicht entladenen Initial-Strom: {E_0[interval[-1]].solution_value() * -P_loaded:.1f}, Gewinn durch Batterie Füllstand: {E_B.solution_value() * min_price}")
    print(f"{costs_with_balancing}, {costs_initial_energy:.1f}, {E_0[interval[-1]].solution_value() * -P_loaded}, {E_B.solution_value() * min_price:.1f}")
    print(f"{costs_with_balancing}, {costs_initial_energy:.1f}, {E_0[interval[-1]].solution_value()} * {-P_loaded}, {E_B.solution_value()} * {min_price:.1f}, {avg_price}")

    return soc_list, energy_bought_list, battery_discharge_list,battery_charge_list, solar_energy_list,is_charging_list, is_discharging_list, outside_to_battery_list,solar_to_battery_list