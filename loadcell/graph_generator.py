import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import List
from ingest import *

flight_data = pd.read_csv('../data/FlightData.csv')
flight_data["GPS Time (s)"] -= flight_data["GPS Time (s)"][0]

loadcell_0 = pd.read_csv('../data/%s/load_cell_0_readings.csv' % (LOADCELL_DATA_FOLDER))
loadcell_1 = pd.read_csv('../data/%s/load_cell_1_readings.csv' % (LOADCELL_DATA_FOLDER))
loadcell_2 = pd.read_csv('../data/%s/load_cell_2_readings.csv' % (LOADCELL_DATA_FOLDER))
loadcell_3 = pd.read_csv('../data/%s/load_cell_3_readings.csv' % (LOADCELL_DATA_FOLDER))
loadcell_4 = pd.read_csv('../data/%s/load_cell_4_readings.csv' % (LOADCELL_DATA_FOLDER))
loadcell_5 = pd.read_csv('../data/%s/load_cell_5_readings.csv' % (LOADCELL_DATA_FOLDER))
state      = pd.read_csv('../data/%s/state.csv' % (LOADCELL_DATA_FOLDER))

min_time = min([
    loadcell_0["Time"][0],
    loadcell_1["Time"][0],
    loadcell_2["Time"][0],
    loadcell_3["Time"][0],
    loadcell_4["Time"][0],
    loadcell_5["Time"][0],
    state["Time"][0],
])

loadcell_0["Time"] -= min_time
loadcell_1["Time"] -= min_time
loadcell_2["Time"] -= min_time
loadcell_3["Time"] -= min_time
loadcell_4["Time"] -= min_time
loadcell_5["Time"] -= min_time
state["Time"]      -= min_time

parabolas = ReadParabolas()

flight_time = flight_data["GPS Time (s)"]
flight_accel = flight_data["Az (m/s^2)"]

plt.plot(flight_time, flight_accel)
plt.hlines([-MICRO_G_ENTRY_THRESHOLD, -MICRO_G_EXIT_THRESHOLD, -9.8], min(flight_time), max(flight_time))
plt.vlines([p.start for p in parabolas], min(flight_accel), max(flight_accel), color="r")
plt.vlines([p.end for p in parabolas], min(flight_accel), max(flight_accel), color="g")

plt.plot(loadcell_0["Time"] + 390, loadcell_0["Reading"]/1e6)

plt.show()