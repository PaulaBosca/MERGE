from typing import List, Callable

def LinearInterpolation(t1: float, x1: float, t2: float, x2: float, t: float) -> float:
    return (x2 - x1)*((t - t1)/(t2 - t1)) + x1

class TimeseriesNode:
    def __init__(self, t: float, x: float, left, right):
        self.t = t
        self.x = x
        self.left = left
        self.right = right

def BuildTree(ts: List[float], vals: List[float]) -> TimeseriesNode:
    if len(ts) == 1:
        return TimeseriesNode(ts[0], vals[0], None, None)
    elif len(ts) == 2:
        return TimeseriesNode(ts[0], vals[0], None, TimeseriesNode(ts[1], vals[1], None, None))
    elif len(ts) >= 3:
        middle_i = (len(ts) - 1) // 2
        return TimeseriesNode(ts[middle_i], vals[middle_i], 
                            BuildTree(ts[:middle_i], vals[:middle_i]), 
                            BuildTree(ts[middle_i + 1:], vals[middle_i + 1:]))

class Timeseries:
    def __init__(self, ts: List[float], vals: List[float], interpolator: Callable[[float, float, float, float, float], float]):
        self.ts = ts
        self.vals = vals
        self.interpolator = interpolator
        self.root = BuildTree(ts, vals)

    def get(self, t: float) -> float:
        return 0