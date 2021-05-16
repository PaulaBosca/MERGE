import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Tuple, List, Callable
import os

def sliceHeightTimeGraph(csv_data: pd.DataFrame, lines: List[Tuple[str, Callable[[pd.DataFrame], List[float]] ]], out_file: str):
    time = csv_data["Time"]
    
    fig, ax = plt.subplots()
    for line in lines:
        data = line[1](csv_data)
        plotLine, = ax.plot(time, data)
        plotLine.set_label(line[0])

    ax.legend()
    ax.set(xlabel='Time (s)', ylabel='Height (cm)', title=out_file)
    ax.grid()
    # fig.savefig(out_file)
    
def multiLineGraph(csv_data: pd.DataFrame, frames: List[int], filename: str):
    fig, ax = plt.subplots()

    horizontal_positions = [-3, -2, -1, 0, 1, 2, 3]
    for frame in frames:
        #TODO(Jon): use the average max values of the prev/next n frames to help smooth things out
        heights = [
            csv_data["Tank 1 Slice 1 Max"][frame],
            csv_data["Tank 1 Slice 2 Max"][frame],
            csv_data["Tank 1 Slice 3 Max"][frame],
            csv_data["Tank 1 Slice 4 Max"][frame],
            csv_data["Tank 1 Slice 5 Max"][frame],
            csv_data["Tank 1 Slice 6 Max"][frame],
            csv_data["Tank 1 Slice 7 Max"][frame],
        ]
        ax.plot(horizontal_positions, heights)

    ax.set(xlabel='Horizontal Position (???)', ylabel='Height (cm)', title=filename)
    ax.grid()
    # fig.savefig(filename)

def outputGraph(file):
    print(f"loading ../out/video/{file}")
    csv_data = pd.read_csv(f"../out/video/{file}")
    
    # Generate graphs
    sliceHeightTimeGraph(csv_data, [
        ("Tank 1", lambda data: [ max(
            data["Tank 1 Slice 1 Max"][i],
            data["Tank 1 Slice 2 Max"][i],
            data["Tank 1 Slice 3 Max"][i],
            # data["Tank 1 Slice 4 Max"][i],
            data["Tank 1 Slice 5 Max"][i],
            data["Tank 1 Slice 6 Max"][i],
            data["Tank 1 Slice 7 Max"][i],
        ) for i in range(len(data["Time"])) ]),
        ("Tank 2", lambda data: [ max(
            data["Tank 2 Slice 1 Max"][i],
            data["Tank 2 Slice 2 Max"][i],
            data["Tank 2 Slice 3 Max"][i],
            # data["Tank 2 Slice 4 Max"][i],
            data["Tank 2 Slice 5 Max"][i],
            data["Tank 2 Slice 6 Max"][i],
            data["Tank 2 Slice 7 Max"][i],
        ) for i in range(len(data["Time"])) ]),
        ("Tank 3", lambda data: [ max(
            data["Tank 3 Slice 1 Max"][i],
            data["Tank 3 Slice 2 Max"][i],
            data["Tank 3 Slice 3 Max"][i],
            # data["Tank 3 Slice 4 Max"][i],
            data["Tank 3 Slice 5 Max"][i],
            data["Tank 3 Slice 6 Max"][i],
            data["Tank 3 Slice 7 Max"][i],
        ) for i in range(len(data["Time"])) ]),
    ], f"../out/video/{file}.png")

# for file in os.listdir("../out/video/"):
#     if file.endswith("_slice7_filtered.csv"):
#         outputGraph(file)

prefix = "0to681"
outputGraph(f"{prefix}_slice7_filtered.csv")
outputGraph(f"{prefix}_slice7_raw.csv")

plt.show()