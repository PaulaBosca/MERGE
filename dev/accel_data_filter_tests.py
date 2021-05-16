# Filename: accel_data_filter_tests.py  SRC: J.Coppens 2020

import parser
import analytics_config as config
import matplotlib.pyplot as plt

def exponential_smoothing(data, alpha):
    filtered_data = [0]*len(data)
    filtered_data[0] = data[0]
    for i, x in enumerate(data[1:]):
        filtered_data[i+1] = alpha * x + (1 - alpha) * filtered_data[i]
    return filtered_data

accel_data = parser.flight_data('z-acceleration', -1, 'acceleration', config.ACCEL_DATA, datacol=12)

parsed_time = [accel_data.time[0]]
parsed_readings = [accel_data.readings[0]]
for t, a in zip(accel_data.time[1:], accel_data.readings[1:]):
    if (t != parsed_time[-1]):
        parsed_time.append(t)
        parsed_readings.append(a)
accel_data.time = parsed_time
accel_data.readings = parsed_readings
    
accel_data.readings = [a/-9.81 for a in accel_data.readings]

plt.plot(accel_data.time, accel_data.readings, 'k-', linewidth=3)
for a in range(1, 10):
    print(a* 0.1)
    filt = exponential_smoothing(accel_data.readings, a * 0.1)
    plt.plot(accel_data.time, filt, zorder=10-a, label=f"alpha={a * 0.1}", linewidth=1)
plt.legend(loc='best')
plt.ylabel("Z-Acceleration (g-units)")
plt.xlabel("Time")
plt.title("Acceleration Data with Varied Exponential Filter")
plt.show()

plt.plot(accel_data.time, accel_data.readings, 'k-', linewidth=3)
for i, a in enumerate(range(10, 35, 5)):
    print(a / 100)
    filt = exponential_smoothing(accel_data.readings, a / 100)
    plt.plot(accel_data.time, filt, zorder=10-i, label=f"alpha={a / 100}", linewidth=1)
plt.legend(loc='best')
plt.ylabel("Z-Acceleration (g-units)")
plt.xlabel("Time")
plt.title("Acceleration Data with Varied Exponential Filter")
plt.show()
