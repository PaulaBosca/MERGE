import pandas as pd
import json
from typing import List
import scipy.optimize as optimize

LOADCELL_DATA_FOLDER = "7_24_15_10_30"
MICRO_G_ENTRY_THRESHOLD = 0.2
MICRO_G_EXIT_THRESHOLD = 0.5
MIN_PARABOLA_TIME = 10

class StateTimeRange:
    def __init__(self, state: str, start: float, end: float):
        self.state = state
        self.start = start
        self.end = end

def StateTimeRangeToJson(s: StateTimeRange) -> str:
    return json.dumps({
        "state": s.state,
        "start": s.start,
        "end": s.end
    }, indent=4)

def JsonToStateTimeRange(json_str: str) -> StateTimeRange:
    json_dict = json.loads(json_str)
    return StateTimeRange(json_dict["state"], json_dict["start"], json_dict["end"])

def WriteStateTransitions(state_transitions: List[StateTimeRange]):
    with open("../out/state_transitions.json", "w") as f:
        f.write(json.dumps([json.loads(StateTimeRangeToJson(s)) for s in state_transitions], indent=4))

def ReadStateTransitions() -> List[StateTimeRange]:
    with open("../out/state_transitions.json", "r") as f:
        json_list = json.loads(f.read())
        return [JsonToStateTimeRange(json.dumps(d)) for d in json_list]
        
class ParabolaTimeRange:
    def __init__(self, start: float, end: float):
        self.start = start
        self.end = end

def ParabolaTimeRangeToJson(s: ParabolaTimeRange) -> str:
    return json.dumps({
        "start": s.start,
        "end": s.end
    }, indent=4)

def JsonToParabolaTimeRange(json_str: str) -> ParabolaTimeRange:
    json_dict = json.loads(json_str)
    return ParabolaTimeRange(json_dict["start"], json_dict["end"])

def WriteParabolas(parabolas: List[ParabolaTimeRange]):
    with open("../out/parabolas.json", "w") as f:
        f.write(json.dumps([json.loads(ParabolaTimeRangeToJson(s)) for s in parabolas], indent=4))

def ReadParabolas() -> List[ParabolaTimeRange]:
    with open("../out/parabolas.json", "r") as f:
        json_list = json.loads(f.read())
        return [JsonToParabolaTimeRange(json.dumps(d)) for d in json_list]

def FitError(params) -> float:
    A = params[0]
    B = params[0]
    T0 = params[0]
    return abs(A**2 + B**2)

if __name__ == "__main__":
    # Load & zero all of our data
    print("Loading and zeroing from %s" % (LOADCELL_DATA_FOLDER))
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

    # Load & zero flight data
    print("Loading and zeroing from flight data")
    flight_data = pd.read_csv('../data/FlightData.csv')
    flight_data["GPS Time (s)"] -= flight_data["GPS Time (s)"][0]

    #Find state transitions from "state" dataframe
    print("Finding state transitions")
    state_transitions = []
    curr_state = StateTimeRange(state["State"][0], state["Time"][0], state["Time"][0])
    for i in range(len(state.index)): 
        curr_row = state.iloc[i]
        curr_state.end = curr_row["Time"]

        if curr_row["State"] != curr_state.state:
            state_transitions.append(curr_state)
            curr_state = StateTimeRange(curr_row["State"], curr_row["Time"], curr_row["Time"])
    state_transitions.append(curr_state)
    
    WriteStateTransitions(state_transitions)

    #Find parabola start & end times from "flight_data" dataframe
    print("Finding parabolas")
    parabolas = []
    curr_parabola = None
    for i in range(len(flight_data.index)):
        accel = -flight_data["Az (m/s^2)"][i]
        time = flight_data["GPS Time (s)"][i]

        if (MICRO_G_ENTRY_THRESHOLD > accel) and (curr_parabola == None):
            curr_parabola = ParabolaTimeRange(time, 0)

        if (accel > MICRO_G_EXIT_THRESHOLD) and (curr_parabola != None) and (time - curr_parabola.start >= MIN_PARABOLA_TIME):
            curr_parabola.end = time
            parabolas.append(curr_parabola)
            curr_parabola = None

    WriteParabolas(parabolas)

    #Fit each of the load cell readings to the flight acceleration
    print("Fitting load cell readings to flight acceleration")
    loadcells = [
        loadcell_0,
        loadcell_1,
        loadcell_2,
        loadcell_3,
        loadcell_4,
        loadcell_5
    ]
    for i in range(len(loadcells)):
        # Params are A, B & T0
        initial_params = [1, 1, 390]
        result = optimize.minimize(lambda params: FitError(params), initial_params)
        print(result.success, result.x, result.message)
