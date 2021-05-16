# Filename: parabola_parser.py  SRC: J.Coppens 2020

import numpy as np
import parser
import analytics_config as config
import copy
import math

def find_parabolas(data):
    parabolas = [[], [], [], []]
    t0 = 0
    i = 1
    for t, a in zip(data.time, data.readings):
        if(abs(a) < config.MICRO_G_ENTRY_THRESHOLD and t0==0):
            t0 = t
        if(abs(a) > config.MICRO_G_EXIT_THRESHOLD and t0>0 and t-t0 > 10):
            #print(f"{i:2d} {t-t0:5.2f} {t0:7.2f} {t:7.2f}")
            parabolas[0].append(i)      #parabola number
            parabolas[1].append(t0)     #start time
            parabolas[2].append(t)      #end time
            parabolas[3].append(t0 - t) #duration
            t0 = 0
            i += 1
    return parabolas

def linear_interpolation(x, p0, p1):
    x0, y0 = p0
    x1, y1 = p1
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)

class parabola:
    def __init__(self, num, start, end, data, procedure):
        self.num = num
        self.start = start
        self.end = end
        self.name = "Parabola " + str(num)
        self.data = copy.deepcopy(data)
        self.procedure = procedure
      
        print(f"Parsing {self.name}")
        for cell in self.data:
            idx = np.searchsorted(cell.time, self.start, side="left")
            if idx > 0 and (idx == len(cell.time) or math.fabs(self.start - cell.time[idx-1]) < math.fabs(self.start - cell.time[idx])):
                idx -= 1
            # create data subsets of each of the loadcells
            MIN = idx - 3
            MAX = MIN + 30
            cell.time = cell.time[MIN:MAX]
            cell.readings = cell.readings[MIN:MAX]
            cell.accel = cell.accel[MIN:MAX]

def get_parabola_sets(data, parab_times):
    parab_start = parab_times[1]
    parab_end = parab_times[2]
    parab_list = []
    procedures = ['Control', 'Fill 25%', 'Fill 50%', 'Fill 75%']
    for i, (t_start, t_end) in enumerate(zip(parab_start, parab_end)):
        parab_list.append(parabola(i+1, t_start, t_end, data, procedures[i%4]))
    return parab_list
    
if __name__ == "__main__":
    accel = parser.flight_data('z-acceleration', -1, 'acceleration', config.ACCEL_DATA, datacol=12)
    accel.zero_times(accel.time[0] + config.OFFSET)

    p = find_parabolas(accel)
    
    with open(config.PARABOLAS, 'w+') as f:
        f.write('parabola, start_time, end_time, duration\r\n')
        for i in range(len(p[0])):
            f.write("%d, %.4f, %.4f, %.4f\r\n" % (p[0][i], p[1][i], p[2][i], p[3][i]))
