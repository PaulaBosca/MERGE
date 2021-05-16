# Filename: flight_data_plotting.py  SRC: J.Coppens 2020

import matplotlib.pyplot as plt
import plotting_utils as utils
import analytics_config as config

def plot_z_acceleration(accel, data, parabola_times, parabola_set):
    '''
    Single plot showing the acceleration data for each load cell in the tank set chosen
    and the raw acceleration data.
    
    Args:
        accel: Set this to the acceleration_data variable returned by read_in_data() (defined in 
            plotting_utils.py) to add z-axis acceleration to the plot.
        data: Set this to the data variable returned by read_in_data() (defined in plotting_utils.py). 
            This variable contains 6 processed_flight_data objects , each corresponding the data from
            the 6 different experiment sensors.
        parabola_times: Set this to the parabola_times variable returned by read_in_data() 
            (defined in plotting_utils.py) to add vertical lines to the plot where each parabola starts
            and ends.
        parabola_set: A string that determines which parabola set to plot. For example, setting this 
            to 'Set1 Parabolas' will create a plot showing data from the first set of parabolas 
            (i.e. parabolas 1-4). See definition of get_parabola_xlim() in plotting_utils.py for all 
            acceptable inputs.
    '''
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize = (20,8))

    # Plot data
    utils.add_acceleration_data(ax, accel, g_units=True)
    utils.add_parabola_times(ax, parabola_times)
    for cell in data:
        ax.plot(cell.time, [a/-9.81 for a in cell.accel], utils.cell_style(cell.num), 
                marker='o', markersize=2, zorder=10, linewidth=1)

    # Format plot
    utils.basic_formatting(ax)
    ax.set_title(f"{parabola_set} Z-Acceleration", loc='center', fontsize=utils.SIZE+2)
    ax.set_xlim(utils.get_parabola_xlim(parabola_set))

    # Save plot
    filename ="Accel/" + parabola_set.replace(" ","_").lower() + "_accel.png"
    print(f"Plotting {filename}")
    plt.savefig(config.IMGPATH + filename, dpi=300, bbox_inches='tight')

def plot_sensor_data(data, tank_set='All Tanks', parabola_set='All Parabolas', 
        accel=0, parabola_times=0, states=0, raw_data=False):
    '''
    Single plot showing the data for each load cell in the tank set chosen. 
    
    There are optional arguments to set what sensor data is shown (top and/or bottom, merge, control,
    and/or highschool), which parabola (or parabola set) data is shown, and what supplimentary data 
    is shown (acceleration, parabola start/end times, system state).

    Args:
        data: Set this to the data variable returned by read_in_data() (defined in plotting_utils.py). 
            This variable contains 6 processed_flight_data objects , each corresponding the data from
            the 6 different experiment sensors.
        tank_set: A string that determines which subset of sensor data to use. For example, setting 
            this to 'Top Tanks' will create a plot that only shows data from the sensors that were 
            at the top of each tank. See definition of get_data_subset() in plotting_utils.py for all 
            acceptable inputs.
        parabola_set: A string that determines which parabola set to plot. For example, setting this 
            to 'Set1 Parabolas' will create a plot showing data from the first set of parabolas 
            (i.e. parabolas 1-4). See definition of get_parabola_xlim() in plotting_utils.py for all 
            acceptable inputs.
        accel: Set this to the acceleration_data variable returned by read_in_data() (defined in 
            plotting_utils.py) to add z-axis acceleration to the plot.
        parabola_times: Set this to the parabola_times variable returned by read_in_data() 
            (defined in plotting_utils.py) to add vertical lines to the plot where each parabola starts
            and ends.
        states: Set this to the states variable returned by read_in_data() (defined in plotting_utils.py) 
            to add a horizontal bar plot that denotes the state of the system at any given time (idle, 
            reset, filling 25%, filling 50%, and filling 75%).
            and ends.
        raw_data: Boolean value, set to true if 'data' argument is unprocessed raw data.
    '''
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize = (20,8))
    
    # Plot data
    for cell in utils.get_data_subset(tank_set, data):
        ax.plot(cell.time, cell.readings, utils.cell_style(cell.num), label=cell.name, zorder=5)
    
    # Plot acceleration data
    if(accel != 0):
        ax2 = plt.twinx()
        utils.add_acceleration_data(ax2, accel, g_units=True)
    
    # Add parabola times
    if(parabola_times != 0):
        utils.add_parabola_times(ax, parabola_times)
    
    # Add state settings bar
    if(states != 0):
        utils.add_state_settings_bar(ax, states, ypos=-500000, bar_size=10000)

    # Format x/y axes
    ax.set_ylabel('Sensor Output', fontsize=utils.SIZE)
    ax.set_xlim(utils.get_parabola_xlim(parabola_set))
    ax.set_xlabel('Time (s)', fontsize = utils.SIZE)

    # Format plot
    ax2 = ax2 if accel != 0 else 0
    utils.basic_formatting(ax, ax2=ax2)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc='upper center', fontsize=utils.SIZE, ncol=3, bbox_to_anchor=(0.5,-0.1))
    title = f"{tank_set} {parabola_set}"
    title = f"{title} Raw Data" if raw_data else title
    ax.set_title(title, loc='center', fontsize=utils.SIZE+2)

    # Save plot 
    filename = f"Regular/{title.replace(' ', '_').lower()}.png"
    print(f"Plotting {filename}")
    plt.savefig(config.IMGPATH + filename, dpi=300, bbox_inches='tight')

def detailed_parabola_plots(parabs, tank_set, accel=0, states=0, zero_to_parab_start=False):
    '''
    12 subplots, each showing the data for each parabola on its own (i.e. the top row is set1 parabolas 
    (#1-4), the middle row is set2 (#5-8), and the final row is set3 (#9-12)

    There are optional arguments to set what sensor data is shown (top and/or bottom, merge, control,
    and/or highschool) and what supplimentary data is shown (acceleration, parabola start/end times, 
    system state).

    Args:
        parabs: Set this to the parabola_data variable returned by read_in_data() (defined in 
            plotting_utils.py). This variable contains 12 parabola objects (defined in 
            parabola_parser.py), each containing sensor and acceleration data for each of the 12
            different parabolas.
        tank_set: A string that determines which subset of sensor data to use. For example, setting 
            this to 'Top Tanks' will create a plot that only shows data from the sensors that were 
            at the top of each tank. See definition of get_data_subset() in plotting_utils.py for all 
            acceptable inputs.
        accel: Set this to the acceleration_data variable returned by read_in_data() (defined in 
            plotting_utils.py) to add z-axis acceleration to the plot.
        states: Set this to the states variable returned by read_in_data() (defined in plotting_utils.py) 
            to add a horizontal bar plot that denotes the state of the system at any given time (idle, 
            reset, filling 25%, filling 50%, and filling 75%).
            and ends.
        zero_to_parab_start: Boolean value. If set to true all plots will have their time-axis (x-axis) 
            set to zero at the time where the parabola of said plot starts.
    '''
    fig, axes = plt.subplots( nrows=3, ncols=4, figsize=(26,18))
    
    for row, axes_row in enumerate(axes):
        for col, ax in enumerate(axes_row):
            ax2 = ax.twinx()
            idx = col + row * 4
            
            # If true, set t=0 to be when the parabola starts
            t0 = parabs[idx].start if zero_to_parab_start else 0

            # Plot data
            data_subset = utils.get_data_subset(tank_set, parabs[idx].data)
            for cell in data_subset:
                ax.plot([t - t0 for t in cell.time], cell.readings, utils.cell_style(cell.num), label=cell.name, zorder=5, marker='o', markersize=2)

            # Add acceleration 
            ax2.plot([t - t0 for t in accel.time], [a/-9.81 for a in accel.readings], 'k-', zorder=1)
            ax2.set_ylim(-0.05, 0.2)

            # Add parabola times
            ax.axvline(x=parabs[idx].start - t0, linewidth=1.5, color='k', linestyle='--', zorder=10)
            ax.axvline(x=parabs[idx].end   - t0, linewidth=1.5, color='k', linestyle='--', zorder=10)

            # Add state settings bar
            if (states != 0):
                utils.add_state_settings_bar(ax, states, ypos=-4.5e5, bar_size=0.2e5, zero_time=t0)

            # Format x/y axes
            ax.set_xlim(cell.time[0] - t0, cell.time[-1] - t0)
            ax.set_ylim(-5e5, 0e5)
            if (row == 2):
                ax.set_xlabel("Time (s)", fontsize=utils.SIZE)
            if (col == 0):
                ax.set_ylabel("Sensor Output", fontsize=utils.SIZE)
            if (col == 3):
                ax2.set_ylabel("Acceleration (g units)", fontsize=utils.SIZE, rotation=270, labelpad=15)

            # Format subplot axis
            ax.text(0.1, 1.01, f"{parabs[idx].name}: {parabs[idx].procedure}", 
                    horizontalalignment='left', fontsize=utils.SIZE, transform=ax.transAxes)
            utils.basic_formatting(ax, ax2=ax2)
    
    # Format plot
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', fontsize=utils.SIZE, ncol=3)
    title = tank_set  + " Breakdown"
    fig.suptitle(title, y=0.94, fontsize=30)

    # Save plot
    filename = "Detailed/breakdown_" + tank_set.replace(" ", "_").lower() + ".png"
    print(f"Plotting {filename}")
    plt.savefig(config.IMGPATH + filename, dpi=500, bbox_inches='tight')

def detailed_parabola_ratio_plots(parabs, tank_set, accel=0, states=0, zero_to_parab_start=False, 
        output_type="Ratio Plots"):
    '''
    9 subplots, each showing the data for each fill parabola (25%,50%,75%) divided by the control 
    for its set.
    
    For example, top row is all set1 fill parabolas (parabolas #2,3,4) divided by the control parabola 
    for set1 (parabola #1)).

    There are optional arguments to set what sensor data is shown (top and/or bottom, merge, control,
    and/or highschool) and what supplimentary data is shown (acceleration, parabola start/end times, 
    system state).

    Args:
        parabs: Set this to the parabola_data variable returned by read_in_data() (defined in 
            plotting_utils.py). This variable contains 12 parabola objects (defined in 
            parabola_parser.py), each containing sensor and acceleration data for each of the 12
            different parabolas.
        tank_set: A string that determines which subset of sensor data to use. For example, setting 
            this to 'Top Tanks' will create a plot that only shows data from the sensors that were 
            at the top of each tank. See definition of get_data_subset() in plotting_utils.py for all 
            acceptable inputs.
        accel: Set this to the acceleration_data variable returned by read_in_data() (defined in 
            plotting_utils.py) to add z-axis acceleration to the plot.
        states: Set this to the states variable returned by read_in_data() (defined in plotting_utils.py) 
            to add a horizontal bar plot that denotes the state of the system at any given time (idle, 
            reset, filling 25%, filling 50%, and filling 75%).
            and ends.
        zero_to_parab_start: Boolean value. If set to true all plots will have their time-axis (x-axis) 
            set to zero at the time where the parabola of said plot starts.
        output_type: A string. Determines what type of data to plot. Options are either the default ratio
        plot (test data/ control data), effective mass plot, or ratio plot with acceleration ration factored 
        in.
    '''
    fig, axes = plt.subplots(nrows=3, ncols=3, figsize=(26,18))
        
    controls = parabs[0::4]
    sets = [ parabs[1:4], parabs[5:8], parabs[9:] ]
    
    for row, axes_row in enumerate(axes):
        control_parab = controls[row]
        control_data = utils.get_data_subset(tank_set, control_parab.data)
        for col, ax in enumerate(axes_row):
            ax2 = ax.twinx()
            idx = col + row * 3
            test_parab = sets[row][col]
            test_data = utils.get_data_subset(tank_set, test_parab.data)
            
            # If true, set t=0 to be when the parabola starts
            t0 = test_parab.start if zero_to_parab_start else 0
            
            # Plot data
            for test, ctrl in zip(test_data, control_data):
                effective_mass = [tr/at - cr/ac for tr, at, cr, ac in zip(test.readings, test.accel, ctrl.readings, ctrl.accel)]
                accel_ratio = [at/ac for at, ac in zip(test.accel, ctrl.accel)]
                sensor_ratio = [t/c for t, c in zip(test.readings, ctrl.readings)]
                sensor_accel_ratio = [s / a for s, a in zip(sensor_ratio, accel_ratio)]
                print(effective_mass[0], effective_mass[-1])
                print(sensor_ratio[0], sensor_ratio[-1])
                # output = sensor_ratio
                # output = effective_mass if (output_type == "Effective Mass") else sensor_ratio
                # output = sensor_accel_ratio if (output_type == "Accel Ratio") else sensor_ratio
                # ax.plot([t - t0 for t in test.time], output, utils.cell_style(test.num), label=test.name, zorder=5)
                ax.plot([t - t0 for t in test.time], effective_mass, utils.cell_style(test.num), label=test.name, zorder=5)

            ############## WIP ##################
            # Add acceleration 
            ax2.plot([t - t0 for t in accel.time], [a/-9.81 for a in accel.readings], 'k-', zorder=1)
            ax2.set_ylim(-0.05, 0.2)
            #####################################

            # Add parabola times
            ax.axvline(x=test_parab.start - t0, linewidth=1.5, color='k', linestyle='--', zorder=10)
            ax.axvline(x=test_parab.end - t0,   linewidth=1.5, color='k', linestyle='--', zorder=10)

            # Add state settings bar
            if (states != 0):
                utils.add_state_settings_bar(ax, states, ypos=1.145, bar_size=0.01, zero_time = t0)
            
            # Format x/y axes
            ax.set_xlim(test.time[0] - t0, test.time[-1] - t0)
            ylim = (0.8, 1.15)
            ylim = (-5e7, 5e7) if (output_type == "Effective Mass") else ylim
            ylim = (-5,5) if (output_type == "Accel Ratio") else ylim
            ax.set_ylim(ylim)
            if (row == 2):
                ax.set_xlabel("Time (s)", fontsize=utils.SIZE)
            if (col == 0):
                ylabel = "Test Output/Control Output"
                ylabel = "Effective Mass" if (output_type == "Effective Mass") else ylabel
                ylabel = "Test/Control * Accel Ratio" if (output_type == "Accel Ratio") else ylabel
                ax.set_ylabel(ylabel, fontsize=utils.SIZE-2)
            if (col == 2):
                ax2.set_ylabel("Acceleration (g units)", fontsize=utils.SIZE, rotation=270, labelpad=15)
            
            # Format subplot axis
            ax.text(0, 1.01, f"{test_parab.name}: {test_parab.procedure}", 
                    horizontalalignment='left', fontsize=utils.SIZE+4, transform=ax.transAxes)
            utils.basic_formatting(ax, ax2=ax2)
    
    # Format plot
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', fontsize=utils.SIZE, ncol=3) 
    title = f"{tank_set} Ratio Plots (fill/control)"
    title = f"{tank_set} Effective Mass" if (output_type == "Effective Mass") else title
    title = f"{tank_set} Ratio * Accel Ratio: (fill/fill accel)*(control accel/control)" if (output_type == "Accel Ratio") else title
    fig.suptitle(title, y=0.94, fontsize=30)

    # Save plot
    filename = f"Detailed_Ratio/{output_type.replace(' ', '_').lower()}_{tank_set.replace(' ', '_').lower()}.png"
    print(f"Plotting {filename}")
    plt.savefig(config.IMGPATH + filename, dpi=500, bbox_inches='tight')

def detailed_parabola_accel_ratio_plots(parabs, tank_set, accel=0, states=0, zero_to_parab_start=False):
    '''
    9 subplots, each showing the data accelration for each fill parabola (25%,50%,75%) divided by 
    the control for its set.
    
    For example, top row is all set1 fill parabolas (parabolas #2,3,4) divided by the control parabola 
    for set1 (parabola #1)).

    There are optional arguments to set what sensor data is shown (top and/or bottom, merge, control,
    and/or highschool) and what supplimentary data is shown (acceleration, parabola start/end times, 
    system state).

    Args:
        parabs: Set this to the parabola_data variable returned by read_in_data() (defined in 
            plotting_utils.py). This variable contains 12 parabola objects (defined in 
            parabola_parser.py), each containing sensor and acceleration data for each of the 12
            different parabolas.
        tank_set: A string that determines which subset of sensor data to use. For example, setting 
            this to 'Top Tanks' will create a plot that only shows data from the sensors that were 
            at the top of each tank. See definition of get_data_subset() in plotting_utils.py for all 
            acceptable inputs.
        accel: Set this to the acceleration_data variable returned by read_in_data() (defined in 
            plotting_utils.py) to add z-axis acceleration to the plot.
        states: Set this to the states variable returned by read_in_data() (defined in plotting_utils.py) 
            to add a horizontal bar plot that denotes the state of the system at any given time (idle, 
            reset, filling 25%, filling 50%, and filling 75%).
            and ends.
        zero_to_parab_start: Boolean value. If set to true all plots will have their time-axis (x-axis) 
            set to zero at the time where the parabola of said plot starts.
    '''
    fig, axes = plt.subplots(nrows=3, ncols=3, figsize=(26,18))
        
    controls = parabs[0::4]
    sets = [ parabs[1:4], parabs[5:8], parabs[9:] ]
    
    for row, axes_row in enumerate(axes):
        control_parab = controls[row]
        control_data = utils.get_data_subset(tank_set, control_parab.data)
        for col, ax in enumerate(axes_row):
            ax2 = ax.twinx()
            idx = col + row * 3
            test_parab = sets[row][col]
            test_data = utils.get_data_subset(tank_set, test_parab.data)
            
            # If true, set t=0 to be when the parabola starts
            t0 = test_parab.start if zero_to_parab_start else 0
            
            # Plot data
            for test, ctrl in zip(test_data, control_data):
                accel_ratio = [at/ac for at, ac in zip(test.accel, ctrl.accel)]
                ax.plot([t - t0 for t in test.time], accel_ratio, 'k', marker='o', markersize=2, zorder=5)
                ax2.plot([t - t0 for t in test.time], [a/-9.81 for a in test.accel], utils.cell_style(test.num), marker='o', markersize=2, zorder=5)
                ax2.plot([t - t0 for t in test.time], [a/-9.81 for a in ctrl.accel], 'm', marker='o', markersize=2, zorder=5)
            ax2.plot([t - t0 for t in accel.time], [a/-9.81 for a in accel.readings], 'k-', zorder=1)

            # Add parabola times
            ax.axvline(x=test_parab.start - t0, linewidth=1.5, color='k', linestyle='--', zorder=10)
            ax.axvline(x=test_parab.end - t0,   linewidth=1.5, color='k', linestyle='--', zorder=10)
            
            # Add state settings bar
            if (states != 0):
                utils.add_state_settings_bar(ax, states, ypos=1.145, bar_size=0.01, zero_time = t0)
            
            # Format x/y axes
            ax.set_xlim(test.time[0] - t0, test.time[-1] - t0)
            ax.set_ylim(-10, 10)
            ax2.set_ylim(-0.05, 0.2)
            if (row == 2):
                ax.set_xlabel("Time (s)", fontsize=utils.SIZE)
            if (col == 0):
                ax.set_ylabel("Test Accel/Control Accel", fontsize=utils.SIZE-2)
            if (col == 2):
                ax2.set_ylabel("Acceleration (g units)", fontsize=utils.SIZE, rotation=270, labelpad=15)
            
            # Format subplot axis
            ax.text(0, 1.01, f"{test_parab.name}: {test_parab.procedure}", 
                    horizontalalignment='left', fontsize=utils.SIZE+4, transform=ax.transAxes)
            utils.basic_formatting(ax, ax2=ax2)
    
    # Format plot
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', fontsize=utils.SIZE, ncol=3) 
    title = tank_set  + " Acceleration Ratio Plots (fill/control)"
    fig.suptitle(title, y=0.94, fontsize=30)
    
    # Save plot
    filename = f"Accel/accel_ratio_plots_{tank_set.replace(' ', '_').lower()}.png"
    print(f"Plotting {filename}")
    plt.savefig(config.IMGPATH + filename, dpi=500, bbox_inches='tight')
