# Filename: parser.py  SRC: J.Coppens 2020

import numpy as np
import analytics_config as config
import math

class flight_data:    
    def __init__(self, name, n, data_type, path, timecol=0, datacol=1):
        self.num = n
        self.data_type = data_type
        self.name = name
        print(f"Reading in {path}")
        data = np.genfromtxt(path, unpack=False, delimiter=',', skip_header=1, usecols=(timecol, datacol), dtype=None, encoding=None, names=['Time', 'Data'])
        self.time = data['Time']
        self.readings = data['Data']

    def zero_readings(self, d0):
        print(f"Zeroing '{self.name}' readings")
        self.readings = [d - d0 for d in self.readings]   

    def filter_readings(self, cutoff=100000):
        print(f"Filtering '{self.name}' readings")
        prev_point = self.readings[0]
        y = self.readings
        t = self.time
        for i, point in enumerate(self.readings):
            if (abs(point - prev_point) > cutoff):
                self.readings[i] = y[i-2] + ((y[i-1]-y[i-2])/(t[i-1]-t[i-2]))*(t[i]-t[i-2]) #linear interpolation
            prev_point = point

    def zero_times(self, t0):
        print(f"Zeroing '{self.name}' times")
        self.time = [t - t0 for t in self.time]

    def downsample(self):
        print(f"Downsampling '{self.name}' times")
        t_prev = -1
        downsampled_time = []
        downsampled_readings = []
        for i, t in enumerate(self.time):
            if(t - t_prev > 0.59): 
                downsampled_time.append(t)
                downsampled_readings.append(self.readings[i])
                t_prev = t
        self.time = downsampled_time
        self.readings = downsampled_readings

    def summary(self, frmat):
        print(f"======== {self.name} ==========")
        print("   Time     Reading")
        for i in range(10):
            print(f"{self.time[i]:>7.2f}  {self.readings[i]:{frmat}}")
        print(f"({len(self.time)}, {len(self.readings)}) total readings")

    def str_to_num(self):
        new_states = []
        for string in self.readings:
            if string == 'Idle':
                new_states.append(0)
            elif string == 'Reset':
                new_states.append(-1)
            elif string == 'Fill %25':
                new_states.append(25)
            elif string == 'Fill %50':
                new_states.append(50)
            elif string == 'Fill %75':
                new_states.append(75)
        self.readings = new_states
        
    def match_accel_data(self, accel_data_time, accel_data):
        self.accel = []
        for n, t_data in enumerate(self.time):
            idx = np.searchsorted(accel_data_time, t_data, side="left")
            if idx > 0 and (idx == len(accel_data_time) 
                    or math.fabs(t_data - accel_data_time[idx-1]) < math.fabs(t_data - accel_data_time[idx])):
                idx -= 1
            self.accel.append(accel_data[idx])
            if (n % 1000 == 999 or n == len(self.time) - 1):
                print(f"'{self.name}' {n+1} of {len(self.time)} accel values found.")

def linear_interpolation(x, p0, p1):
    x0, y0 = p0
    x1, y1 = p1
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)

def exponential_smoothing(data, alpha):
    filtered_data = [0]*len(data)
    filtered_data[0] = data[0]
    for i, x in enumerate(data[1:]):
        filtered_data[i+1] = alpha * x + (1 - alpha) * filtered_data[i]
    return filtered_data

def get_data():
    import parabola_parser
    import copy
    
    # Load in Data
    accel_data = flight_data('z-acceleration', -1, 'acceleration', config.ACCEL_DATA, datacol=12)
    state_data = flight_data('States', -1, 'state', config.DATAPATH + 'state.csv')
    loadcell_data = [
        flight_data('Merge Top',         0, 'load_cell', config.DATAPATH + 'load_cell_0_readings.csv'),
        flight_data('Merge Bottom',      1, 'load_cell', config.DATAPATH + 'load_cell_1_readings.csv'),
        flight_data('Control Top',       2, 'load_cell', config.DATAPATH + 'load_cell_2_readings.csv'),
        flight_data('Control Bottom',    3, 'load_cell', config.DATAPATH + 'load_cell_3_readings.csv'),
        flight_data('Highschool Top',    4, 'load_cell', config.DATAPATH + 'load_cell_4_readings.csv'),
        flight_data('Highschool Bottom', 5, 'load_cell', config.DATAPATH + 'load_cell_5_readings.csv')]

    # Remove duplicate data from accel_data
    parsed_time = [accel_data.time[0]]
    parsed_readings = [accel_data.readings[0]]
    for t, a in zip(accel_data.time[1:], accel_data.readings[1:]):
        if (t != parsed_time[-1]):
            parsed_time.append(t)
            parsed_readings.append(a)
    accel_data.time = parsed_time
    accel_data.readings = parsed_readings
    accel_data.readings = exponential_smoothing(accel_data.readings, alpha=0.2)

    # Format data (zero times, filter 
    t0 = loadcell_data[0].time[0]
    for cell in loadcell_data:
        cell.zero_times(t0)
        cell.filter_readings()
    state_data.zero_times(t0)
    accel_data.zero_times(accel_data.time[0] + config.OFFSET)
    state_data.str_to_num()

    raw_data = copy.deepcopy(loadcell_data)

    # Process Data
    for cell in loadcell_data:
        cell.zero_readings(cell.readings[0])
        cell.downsample()
    state_data.downsample()
    processed_data = loadcell_data
    
    # Match acceleration data to loadcell data time
    for cell in processed_data:
        cell.match_accel_data(accel_data.time[12000:165000], accel_data.readings[12000:165000])

    return raw_data, accel_data, state_data, processed_data

if __name__ == "__main__":

    raw_data, accel_data, state_data, processed_data = get_data()
    
    with open(config.PROCESSED_DATA, 'w+') as f:
        # logging.info("Writing processed data to file/")
        print("Writing processed data to file/")
        f.write("Merge Top, , ,"
                +"Merge Bottom, , ,"
                +"Control Top, , ,"
                +"Control Bottom, , ,"
                +"Highschool Top, , ,"
                +"Highschool Bottom, , ,"
                +"State, \r\n")
        f.write("Time_Cell0,Cell0,Accel_Cell0,"
                +"Time_Cell1,Cell1,Accel_Cell1,"
                +"Time_Cell2,Cell2,Accel_Cell2,"
                +"Time_Cell3,Cell3,Accel_Cell3,"
                +"Time_Cell4,Cell4,Accel_Cell4,"
                +"Time_Cell5,Cell5,Accel_Cell5,"
                +"Time_State,State\r\n")
        for i in range(len(processed_data[0].time)):
            f.write("%.4f,%f,%f,%.4f,%f,%f,%.4f,%f,%f,%.4f,%f,%f,%.4f,%f,%f,%.4f,%f,%f,%.4f,%f\r\n" % (  
                processed_data[0].time[i], processed_data[0].readings[i],processed_data[0].accel[i],
                processed_data[1].time[i], processed_data[1].readings[i],processed_data[1].accel[i],
                processed_data[2].time[i], processed_data[2].readings[i],processed_data[2].accel[i],
                processed_data[3].time[i], processed_data[3].readings[i],processed_data[3].accel[i],
                processed_data[4].time[i], processed_data[4].readings[i],processed_data[4].accel[i],
                processed_data[5].time[i], processed_data[5].readings[i],processed_data[5].accel[i],
                state_data.time[i], state_data.readings[i]))
        
    with open(config.RAW_DATA, 'w+') as f:
        # logging.info("Writing raw data to file.")
        print("Writing raw data to file.")
        f.write("Time_Cell0,Cell0,"
                +"Time_Cell1,Cell1,"
                +"Time_Cell2,Cell2,"
                +"Time_Cell3,Cell3,"
                +"Time_Cell4,Cell4,"
                +"Time_Cell5,Cell5,"
                +"Time_State,State\r\n")
        for i in range(len(raw_data[0].time)):
            f.write("%.4f,%f,%.4f,%f,%.4f,%f,%.4f,%f,%.4f,%f,%.4f,%f,%.4f,%f\r\n" % (  
                raw_data[0].time[i], raw_data[0].readings[i],
                raw_data[1].time[i], raw_data[1].readings[i],
                raw_data[2].time[i], raw_data[2].readings[i],
                raw_data[3].time[i], raw_data[3].readings[i],
                raw_data[4].time[i], raw_data[4].readings[i],
                raw_data[5].time[i], raw_data[5].readings[i],
                state_data.time[i], state_data.readings[i]))
