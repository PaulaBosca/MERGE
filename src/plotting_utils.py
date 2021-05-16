# Filename: plotting_utils.py  SRC: J.Coppens 2020

import analytics_config as config
import numpy as np
import pandas as pd
import parabola_parser
import parser

SIZE = 18

def cell_style(num):
    if num == 0:
        return 'b-'
    elif num == 1:
        return 'b--'
    elif num == 2:
        return 'g-'
    elif num == 3:
        return 'g--'
    elif num == 4:
        return 'r-'
    elif num == 5:
        return 'r--'

def state_color(state):
    if state == 0:
        return 'b'
    elif state == -1:
        return 'r'
    elif state == 25:
        return 'g'
    elif state == 50:
        return 'y'
    elif state == 75:
        return 'c'

def basic_formatting(ax, ax2=0):
    ax.tick_params(direction = 'in', size = 8, top = True, labelsize=SIZE-2)
    ax.ticklabel_format(axis='y', style='sci', scilimits=(0,2))
    ax.grid()
    if (ax2):
        ax2.tick_params(direction = 'in', left=False, right=True, size = 6, labelsize=SIZE-4)
        ax.set_zorder(ax2.get_zorder()+1)   # put ax in front of ax2
        ax.patch.set_visible(False)         # hide the 'canvas'

def add_state_settings_bar(ax, states, ypos, bar_size, zero_time=0):
    time = [t - zero_time for t in states.time]
    prev_state = states.readings[0]
    prev_time = time[0]
    for j, state in enumerate(states.readings):
        if state != prev_state:
            C = state_color(prev_state)
            ax.barh(y=ypos, width=time[j-1]-prev_time, height=bar_size, left=prev_time, color=str(C), zorder=4)
            prev_state = state
            prev_time = time[j-1]

def add_parabola_times(ax, parabolas, zero_time=0):
    for start, end in zip(parabolas[1], parabolas[2]):
        ax.axvline(x=start - zero_time, linewidth=1.5, color='k', linestyle='--', zorder=10)
        ax.axvline(x=end - zero_time, linewidth=1.5, color='k', linestyle='--', zorder=10)

def add_acceleration_data(ax, accel, g_units=True):
    if(g_units == True):
        ax.set_ylabel("Acceleration (g units)", fontsize = SIZE, rotation=270, labelpad=15)
        ax.plot(accel.time, [a/-9.81 for a in accel.readings], 'k-', label='Z-Acceleration', zorder=1, linewidth=0.75)
    else:
        ax.set_ylabel("Acceleration ($m/s^2$)", fontsize = SIZE, rotation=270, labelpad=15)
        ax.plot(accel.time, accel.readings, 'k--', label = 'Z-Acceleration', zorder=1, linewidth=0.75)
    ax.tick_params(size = 8, labelsize=SIZE-2)

def get_data_subset(subset, data):
    if(subset == 'All Tanks'):
        return data
    if(subset == 'Top Tanks'):
        return data[0:6:2]
    if(subset == 'Bottom Tanks'):
        return data[1:6:2]
    if(subset == 'Merge Tank'):
        return data[0:2]
    if(subset == 'Merge Tank Top'):
        return [data[0]]
    if(subset == 'Merge Tank Bottom'):
        return [data[1]]
    if(subset == 'Control Tank'):
        return data[2:4]
    if(subset == 'Control Tank Top'):
        return [data[2]]
    if(subset == 'Control Tank Bottom'):
        return [data[3]]
    if(subset == 'HighSchool Tank'):
        return data[4:6]
    if(subset == 'HighSchool Tank Top'):
        return [data[4]]
    if(subset == 'HighSchool Tank Bottom'):
        return [data[5]]

def get_parabola_xlim(subset):
    if(subset == 'All Parabolas'):
        return config.ALL_PARABOLAS
    if(subset == 'Set1 Parabolas'):
        return config.SET1_PARABOLAS
    if(subset == 'Set2 Parabolas'):
        return config.SET2_PARABOLAS
    if(subset == 'Set3 Parabolas'):
        return config.SET3_PARABOLAS
    if(subset == 'Parabola 1'):
        return config.PARAB01
    if(subset == 'Parabola 2'):
        return config.PARAB02
    if(subset == 'Parabola 3'):
        return config.PARAB03
    if(subset == 'Parabola 4'):
        return config.PARAB04
    if(subset == 'Parabola 5'):
        return config.PARAB05
    if(subset == 'Parabola 6'):
        return config.PARAB06
    if(subset == 'Parabola 7'):
        return config.PARAB07
    if(subset == 'Parabola 8'):
        return config.PARAB08
    if(subset == 'Parabola 9'):
        return config.PARAB09
    if(subset == 'Parabola 10'):
        return config.PARAB10
    if(subset == 'Parabola 11'):
        return config.PARAB11
    if(subset == 'Parabola 12'):
        return config.PARAB12
    print("Error: Parabola subset not an acceptable value.")
    exit()

class processed_flight_data:
    def __init__(self, n, name):
        self.num = n
        self.name = name
        self.time = []
        self.readings = []
        self.accel = []

def read_in_data():
    df = pd.read_csv(config.PROCESSED_DATA, header=[0,1])
    names = [n[0] for n in [col for col in df][::3]]
    data = [processed_flight_data(i, name) for i, name in enumerate(names)][:-1]
    df.columns = df.columns.droplevel()
    for i in range(0,len(df.columns)-2,3):
        idx = int(i/3)
        data[idx].time     = df[df.columns[i+0]].tolist()
        data[idx].readings = df[df.columns[i+1]].tolist()
        data[idx].accel    = df[df.columns[i+2]].tolist()
    
    state_data = processed_flight_data(-1, "States")
    state_data.time = df['Time_State'].tolist()
    state_data.readings = df['State'].tolist()
    
    accel_data = parser.flight_data('z-acceleration', -1, 'acceleration', config.ACCEL_DATA, datacol=12)
    
    parsed_time = [accel_data.time[0]]
    parsed_readings = [accel_data.readings[0]]
    for t, a in zip(accel_data.time[1:], accel_data.readings[1:]):
        if (t != parsed_time[-1]):
            parsed_time.append(t)
            parsed_readings.append(a)
    accel_data.time = parsed_time
    accel_data.readings = parsed_readings
    
    accel_data.zero_times(accel_data.time[0] + config.OFFSET)
    accel_data.readings = parser.exponential_smoothing(accel_data.readings, alpha=0.2)
    
    parabola_times = parabola_parser.find_parabolas(accel_data)
    parabola_data = parabola_parser.get_parabola_sets(data, parabola_times)

    return data, state_data, accel_data, parabola_times, parabola_data
