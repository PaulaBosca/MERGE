# Filename: create_plots.py  SRC: J.Coppens 2020

import parser
import analytics_config as config
import flight_data_plotting as fdplot
from plotting_utils import read_in_data

processed_data, state_data, accel_data, parabola_times, detailed_parab_data,  = read_in_data()

### Acceleration Data
# fdplot.plot_z_acceleration(
#         accel = accel_data, 
#         data = processed_data,
#         parabola_times = parabola_times, 
#         parabola_set = 'Parabola 1')

# fdplot.plot_z_acceleration(
#         accel = accel_data,
#         data = processed_data,
#         parabola_times = parabola_times, 
#         parabola_set = 'Parabola 12')

### Raw Data
# fdplot.plot_sensor_data(
#         data = raw_data, 
#         tank_set = 'All Tanks', 
#         parabola_set = 'All Parabolas', 
#         parabola_times = parabola_times, 
#         raw_data = True)

### Processed Data
# fdplot.plot_sensor_data(
#         data = processed_data, 
#         tank_set = 'Top Tanks', 
#         parabola_set = 'Parabola 1',
#         accel = accel_data,
#         parabola_times = parabola_times,
#         states = state_data,
#         raw_data = False)

# fdplot.plot_sensor_data(
#         data = processed_data, 
#         tank_set = 'All Tanks', 
#         parabola_set = 'All Parabolas',
#         accel = accel_data,
#         parabola_times = parabola_times, 
#         states = state_data,
#         raw_data = False)

# fdplot.plot_sensor_data(
#         data = processed_data, 
#         tank_set = 'Top Tanks',
#         parabola_set = 'Set1 Parabolas', 
#         accel = accel_data,
#         parabola_times = parabola_times,
#         states = state_data)

### Detailed parabola plots
# fdplot.detailed_parabola_plots(
#         parabs = detailed_parab_data, 
#         tank_set = 'Top Tanks',
#         accel = accel_data,
#         states = state_data,
#         zero_to_parab_start = True)

#fdplot.detailed_parabola_plots(
#        parabs = detailed_parab_data, 
#        tank_set = 'Bottom Tanks',
#        accel = accel_data,
#        states = state_data,
#        zero_to_parab_start = True)

### Detailed parabola ratio plots 
# fdplot.detailed_parabola_ratio_plots(
#         parabs = detailed_parab_data, 
#         tank_set = 'Top Tanks',
#         accel = accel_data,
#         states = state_data,
#         output_type = "Ratio Plots",
#         zero_to_parab_start = True)

fdplot.detailed_parabola_ratio_plots(
        parabs = detailed_parab_data, 
        tank_set = 'Top Tanks',
        accel = accel_data,
        states = state_data,
        output_type = "Effective Mass",
        zero_to_parab_start = True)

# fdplot.detailed_parabola_ratio_plots(
#         parabs = detailed_parab_data, 
#         tank_set = 'Top Tanks',
#         accel = accel_data,
#         states = state_data,
#         output_type = "Accel Ratio",
#         zero_to_parab_start = True)

#fdplot.detailed_parabola_ratio_plots(
#        parabs = detailed_parab_data, 
#        tank_set = 'Bottom Tanks',
#        accel = accel_data,
#        states = state_data,
#        zero_to_parab_start = True)

### Detailed parabola acceleration ratio plots 
# fdplot.detailed_parabola_accel_ratio_plots(
#         parabs = detailed_parab_data, 
#         tank_set = 'Top Tanks',
#         accel = accel_data,
#         states = state_data,
#         zero_to_parab_start = True)
