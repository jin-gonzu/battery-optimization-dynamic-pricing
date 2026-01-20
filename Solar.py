
import matplotlib.pyplot as plt
from ortools.linear_solver import pywraplp
from solver import solve_solar
import numpy as np
import re

interval = list(range(96*2))

def readData(filename, length):
    with open(filename) as f:
        data = [float(x) for line in f for x in line.strip().split()[2:]]
    if len(data) != length:
        raise ValueError(f"Unerwartete Anzahl an Daten: {len(data)} statt {length}")
    return data

def read_battery_file(filename):
    with open(filename) as f:
        text = f.read()

    # batsoc extrahieren
    match_batsoc = re.search(r"batsoc\s*:\s*([\d\.]+)", text)
    if match_batsoc:
        battery_soc_initial = float(match_batsoc.group(1))
    else:
        raise ValueError("batsoc not found")

    # socneu extrahieren
    match_soc = re.search(r"socneu\s*:\s*\[([^\]]+)\]", text)
    if match_soc:
        soc_bestehend = [float(x) for x in re.split(r'\s+', match_soc.group(1).strip()) if x]
    else:
        raise ValueError("socneu not found")

    # bezugneu extrahieren
    match_bezug = re.search(r"bezugneu\s*:\s*\[([^\]]+)\]", text)
    if match_bezug:
        bezug_bestehend = [float(x) for x in re.split(r'\s+', match_bezug.group(1).strip()) if x]
    else:
        raise ValueError("bezugneu not found")

    return battery_soc_initial, soc_bestehend, bezug_bestehend

# Beispielaufruf
folderName = "19.20.01"
battery_soc_initial, soc_bestehend, bezug_bestehend = read_battery_file(folderName+"/log.log")

print("Initial SOC:", battery_soc_initial)
print("SOC array:", soc_bestehend[:10], "...")      # nur die ersten 10 Werte
print("Bezug array:", bezug_bestehend[:10], "...")

values_kosten = readData(folderName+"/netztarif.log", len(interval))
energyConsumption = readData(folderName+"/verbrauch.log", len(interval))
values_pv = readData(folderName+"/pv.log", len(interval))

#battery_soc_initial = 70;
battery_soc_target = 35;

battery_soc_minimum_allowed = 35

battery_max_capacity=28800
battery_initial_capacity = int(battery_soc_initial * battery_max_capacity / 100)
battery_target_capacity = int(battery_soc_target * battery_max_capacity / 100)
battery_minimal_capacity = int(battery_soc_minimum_allowed * battery_max_capacity / 100)

battery_charge_power= 1000
battery_discharge_power= 1500

price_selling_energy = 785
price_using_battery = 3080

#lösung bestehendes System
#bezug_bestehend = [
#    2.0, 1.5, 1.2, 1.2, 2.0, 1.4, 1.2, 1.2, 2.1, 1.5, 1.2, 1.2, 2.1, 2.3, 2.1, 2.1, 2.9, 1.7, 1.2, 1.2, 0.0, 0.0, 1.1, 1.1,
#    2.0, 0.9, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
#    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
#    0.0, 0.0, 0.0, 0.0, 0.7, 0.1, 0.0, 0.2, 1.1, 0.5, 0.2, 0.2, 1.1, 0.5, 0.2, 0.2, 1.0, 0.5, 0.2, 0.2, 1.0, 0.4, 0.2, 0.2,
#]

bezug_bestehend_1000 = [v * 1000 for v in bezug_bestehend]

#soc_bestehend = [
#    36.9,40.0,43.0,46.0,49.1,52.1,55.1,58.1,61.2,64.2,67.2,70.3,73.3,76.3,79.4,82.4,85.4,88.5,91.5,94.5,91.0,89.5,92.5,95.5,
#    98.6, 100.0,99.5,99.0,95.5,94.0,93.6,93.1,92.6,92.0,91.5,90.9,90.3,89.7,89.1,88.5,84.9,83.4,82.9,82.6,79.2,77.7,77.1,76.4,
#    72.5,70.7,70.0,69.4,66.0,64.9,65.1,65.6,63.0,62.2,62.1,61.7,58.1,56.7,56.4,56.3,53.3,53.2,52.5,51.8,51.1,50.4,49.7,49.0,
#    48.4,46.8,46.1,45.5,41.2,36.8,33.1,30.0,30.0,30.0,29.9,29.9,29.9,29.9,29.8,29.8,29.8,29.8,29.7,29.7,29.7,29.7,29.6,29.6,
#]

discharge_bestehend = []
for i in range(1, len(soc_bestehend)):
    delta = int((soc_bestehend[i-1] - soc_bestehend[i]) * 28800 / 100)
    discharge_bestehend.append(max(delta, 0))

discharge_bestehend.insert(0, 0)

consumption = {i: int(abs(v) * 1000) for i, v in zip(interval, energyConsumption)}
price_outside_power = {i: int(v * 100) for i, v in zip(interval, values_kosten)}
solar_production = {i: int(v * 1000) for i, v in zip(interval, values_pv)}


soc_optimiert, energy_bought_list, battery_discharge_list, battery_charge_list, solar_energy_list = solve_solar(
    interval=interval,
    consumption=consumption,
    price_outside_power=price_outside_power,
    price_selling_energy=price_selling_energy,
    solar_production=solar_production,
    battery_initial_capacity=battery_initial_capacity,
    battery_minimal_capacity=battery_minimal_capacity,
    battery_charge_power=battery_charge_power,
    battery_discharge_power=battery_discharge_power,
    battery_max_capacity=battery_max_capacity,
    price_using_battery = price_using_battery,
    battery_target_capacity = battery_target_capacity,
    mustLoadFirst =0,
    min_battery_discharge = 23040,
    printEnabled = 1
)

total = sum((e + s) * k for e, s, k in zip(energyConsumption, values_pv, values_kosten))
total_bestehend = sum(e * k for e, k in zip(bezug_bestehend, values_kosten))
total_optimized = sum(e * k for e, k in zip(energy_bought_list, values_kosten))

print(f"Es werden geplant, dass {sum(energyConsumption)} kWh verbraucht werden,\n"
      f"die Kosten ohne Optimierung: {total*-1}, \n"
      f"Die bestehende Optimierung errechnet:{total_bestehend}\n"
      f"Die OR Tools Optimierung errechnet:{total_optimized / 1000:.1f}"
      )

if not soc_optimiert:
    exit()


#draw plots
energyConsumption_plot = [abs(x) * 1000 for x in energyConsumption]
values_kosten_plot = [x * 50 for x in values_kosten]
solar_production_plot = [x for x in solar_production]

fig, axs = plt.subplots(2, 2, figsize=(24, 16))
x = range(len(soc_optimiert))

#PLOT 1
ax = axs[0, 0]
ax.plot(x, soc_optimiert, marker='o', linestyle='-', color='blue', label='SOC OR Tools')
ax.plot(x, soc_bestehend, marker='x', linestyle='--', color='red', label='SOC bestehend')

ax.set_xlabel("Zeitintervall")
ax.set_ylabel("SOC (%)")
ax.set_title("SOC Vergleich")
ax.grid(True)
ax.legend()

#PLOT 2
ax1 = axs[0, 1]
ax1.plot(x, soc_optimiert, marker='o', linestyle='-', color='blue', label='SOC OR Tools')
ax1.plot(x, soc_bestehend, marker='x', linestyle='--', color='red', label='SOC bestehend')
ax1.set_ylabel("SOC (%)")
ax1.grid(True)

ax2 = ax1.twinx()
ax2.plot(x, values_kosten, linestyle=':', marker='s', color='green', label='Preis Netzstrom')
ax2.set_ylabel("Preis (ct/kWh)")

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

ax1.set_title("SOC & Strompreis")

#PLOT 3
ax1 = axs[1, 0]

ax1.plot(x, energyConsumption_plot, linestyle='--', marker='o',
         color='red', label='Verbrauchte Energie')

ax1.bar(x, energy_bought_list, alpha=0.4, color='blue',
        label='Netzbezug optimiert')

ax1.bar(x, battery_discharge_list, alpha=0.4, color='green',
        label='Batterieentladung', bottom=energy_bought_list)

bottom_bar = np.array(energy_bought_list) + np.array(battery_discharge_list)

ax1.bar(x, solar_energy_list, alpha=0.4, color='orange',
        label='Solar Produktion', bottom=bottom_bar)

#ax2 = ax1.twinx()
#ax2.plot(x, values_kosten, linestyle=':', marker='s',
#         color='black', label='Preis Netzstrom')

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

ax1.set_title("Verbrauch & Preis (optimiert)")
ax1.set_ylabel("Energie (Wh)")
ax1.grid(True)

#PLOT 4
ax1 = axs[1, 1]

ax1.plot(x, energyConsumption_plot, linestyle='--', marker='o',
         color='red', label='Verbrauchte Energie')

ax1.bar(x, bezug_bestehend_1000, alpha=0.4, color='blue',
        label='Netzbezug bestehend')

ax1.bar(x, discharge_bestehend, alpha=0.4, color='green',
        label='Batterieentladung', bottom=bezug_bestehend_1000)

bottom_bar = np.array(bezug_bestehend_1000) + np.array(discharge_bestehend)

ax1.bar(x, solar_energy_list, alpha=0.4, color='orange',
        label='Solar Produktion', bottom=bottom_bar)

ax2 = ax1.twinx()
ax2.plot(x, values_kosten, linestyle=':', marker='s',
         color='black', label='Preis Netzstrom')

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

ax1.set_title("Verbrauch & Preis (bestehend)")
ax1.set_ylabel("Energie (Wh)")
ax1.grid(True)

plt.tight_layout()
#plt.show()
plt.savefig(folderName+"\\" + folderName + ".png", dpi=300)