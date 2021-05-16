import cv2
from video_processing import *
import numpy as np
import pandas as pd
import builtins
import os
import sys

def OutputRaw():
    video = cv2.VideoCapture('../data/ExperimentVideo.mp4')
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = video.get(cv2.CAP_PROP_FPS)
    print(str(frame_count) + " Frames")
    print(str(fps) + " FPS")

    tank1, tank2, tank3 = ReadTankSettings()
    markers = ReadVideoMarkers()

    slice_count = 7
    SCALE_PERCENT = 50
    L = 16.192 # cm

    for i in range(len(markers)):
        start_frame = markers[i]
        end_frame = frame_count if i == len(markers) - 1 else markers[i + 1]
        print("Processing frames " + str(start_frame) + " to " + str(end_frame))

        columns = ["Frame", "Time"]
        for slice_i in range(slice_count):
            columns += [
                "Tank 1 Slice " + str(slice_i + 1) + " Min",
                "Tank 1 Slice " + str(slice_i + 1) + " Max",
                "Tank 2 Slice " + str(slice_i + 1) + " Min",
                "Tank 2 Slice " + str(slice_i + 1) + " Max",
                "Tank 3 Slice " + str(slice_i + 1) + " Min",
                "Tank 3 Slice " + str(slice_i + 1) + " Max",
            ]

        raw_data_frame = pd.DataFrame([], columns=columns)
        for frame_i in range(start_frame, end_frame):
            # Get frame
            print("\r" + str(round(100*((frame_i - start_frame)/(end_frame - start_frame - 1)), 2) ) + "%: " + str(frame_i), end="")
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_i)
            _, raw_frame = video.read()

            row = CalculateRow(raw_frame, frame_i, start_frame, fps, slice_count, L, SCALE_PERCENT, tank1, tank2, tank3)
            raw_data_frame = raw_data_frame.append(pd.DataFrame([row], columns=columns), ignore_index=True)

        raw_data_frame.to_csv("../out/video/" + str(start_frame) + "to" + str(end_frame) + "_slice" + str(slice_count) + "_raw.csv", index=False)
        print(f"\rWriting raw data {start_frame}to{end_frame}_slice{slice_count}_raw.csv")

def OutputFiltered():
    for file in os.listdir("../out/video/"):
        if file.endswith("_raw.csv"):
            print(f"Filtering ../out/video/{file}")
            raw_data_frame = pd.read_csv(f"../out/video/{file}")

            filtered_data_frame = pd.DataFrame()
            for column in raw_data_frame.columns:
                if (column == "Frame") or (column == "Time"):
                    filtered_data_frame[column] = raw_data_frame[column]
                else:
                    column_data = raw_data_frame[column]
                    
                    for i in range(3):
                        window = 3
                        column_data = column_data.rolling(window, min_periods=(window//2), center=True).mean()
                    
                    for i in range(1):
                        window = 10
                        column_data = column_data.rolling(window, min_periods=(window//2), center=True).median()

                    filtered_data_frame[column] = column_data
                    print(f"\rDone filtering {column}            ")

            new_file = "../out/video/" + file.replace("_raw.csv", "_filtered.csv")
            filtered_data_frame.to_csv(new_file, index=False)
            print(f"\rDone {new_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Missing argument, pass either 'raw', 'filter' or 'both'")
        sys.exit()

    if sys.argv[1] == "raw":
        OutputRaw()
    elif sys.argv[1] == "filter":
        OutputFiltered()
    elif sys.argv[1] == "both":
        OutputRaw()
        OutputFiltered()
    else:
        print(f"Invalid argument '{sys.argv[1]}'")