import cv2
from typing import Tuple, List
import json
import numpy as np

class HSVRange:
    def __init__(self, minHSV: Tuple[int, int, int], maxHSV: Tuple[int, int, int]):
        self.minHSV = minHSV
        self.maxHSV = maxHSV

    def __str__(self):
        return f"({self.minHSV[0]}, {self.minHSV[1]}, {self.minHSV[2]} to {self.maxHSV[0]}, {self.maxHSV[1]}, {self.maxHSV[2]})"

    def __repr__(self):
        return f"({self.minHSV[0]}, {self.minHSV[1]}, {self.minHSV[2]} to {self.maxHSV[0]}, {self.maxHSV[1]}, {self.maxHSV[2]})"

class TankProcessing:
    def __init__(self, minp: Tuple[float, float], maxp: Tuple[float, float], hsvRanges: List[HSVRange], erosion_size: int, dilation_size: int, min_contour_area: int):
        self.min = minp
        self.max = maxp
        self.hsvRanges = hsvRanges
        self.erosion_size = erosion_size
        self.dilation_size = dilation_size
        self.min_contour_area = min_contour_area

    # Gets the min & max bounds of this tank in pixel coords for a given resolution 
    def getMinMax(self, shape) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        minx = int(self.min[0] * shape[1])
        maxx = int(self.max[0] * shape[1])
        miny = int(self.min[1] * shape[0])
        maxy = int(self.max[1] * shape[0])
        return (minx, miny), (maxx, maxy)
    
    def getSliceMinMax(self, shape, slice_i: int, slice_count: int):
        # Calculate slice x bounds        
        tank_min, tank_max = self.getMinMax(shape)
        slice_min_x = int(tank_min[0] + ((tank_max[0] - tank_min[0]) / slice_count) * slice_i)
        slice_max_x = int(tank_min[0] + ((tank_max[0] - tank_min[0]) / slice_count) * (slice_i + 1))
        return (slice_min_x, tank_min[1]), (slice_max_x, tank_max[1])

    def getMask(self, hsv_frame):
        # Mask based on hsv color ranges
        hsv_mask = np.zeros((hsv_frame.shape[0], hsv_frame.shape[1]), np.uint8)
        for hsvRange in self.hsvRanges:
            hsv_mask |= cv2.inRange(hsv_frame, np.float32(hsvRange.minHSV), np.float32(hsvRange.maxHSV))
        
        # Create tank mask from tank bounds
        tank_min, tank_max = self.getMinMax(hsv_frame.shape)
        tank_mask = np.zeros((hsv_frame.shape[0], hsv_frame.shape[1]), np.uint8)
        cv2.rectangle(tank_mask, tank_min, tank_max, (255), cv2.FILLED)

        # bitwise and tank & hsv range masks together so we only get parts where both were true
        anded_mask = hsv_mask & tank_mask

        # blur mask to smooth out noise
        mask_blurred = cv2.GaussianBlur(anded_mask, (5, 5), 3)

        # erode and dilate so smooth out even more
        mask_eroded = cv2.erode(mask_blurred, np.ones((2*self.erosion_size, 2*self.erosion_size), np.uint8), iterations = 1)
        mask_dilated = cv2.dilate(mask_eroded, np.ones((2*self.dilation_size, 2*self.dilation_size), np.uint8), iterations = 1)
        
        # find largest contour by area, this should be the fluid
        contours, _ = cv2.findContours(mask_dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)        
        areas = [cv2.contourArea(c) for c in contours]
        
        result_mask = np.zeros((hsv_frame.shape[0], hsv_frame.shape[1]), np.uint8)
        if len(contours) > 0:
            largestContourI = np.argmax(areas)
            if areas[largestContourI] > self.min_contour_area:
                cv2.drawContours(result_mask, contours, largestContourI, (255), cv2.FILLED)

        return result_mask

    def getBounds(self, hsv_frame, slice_i: int, slice_count: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        slice_min, slice_max = self.getSliceMinMax(hsv_frame.shape, slice_i, slice_count)
        mask = self.getMask(hsv_frame)
        
        # Create slice mask from tank bounds, slice_i and slice_count
        slice_mask = np.zeros((hsv_frame.shape[0], hsv_frame.shape[1]), np.uint8)
        cv2.rectangle(slice_mask, slice_min, slice_max, (255), cv2.FILLED)

        points = cv2.findNonZero(slice_mask & mask)
        if (points is None) or (len(points) == 0):
            return (slice_min[0], 0), (slice_max[0], 0)
        
        bounding_rect = cv2.boundingRect(points)
        return (slice_min[0], bounding_rect[1]), (slice_max[0], bounding_rect[1] + bounding_rect[3])

def HSVRangeToJson(hsvRange: HSVRange) -> str:
    return json.dumps({
        "minHSV": hsvRange.minHSV,
        "maxHSV": hsvRange.maxHSV
    }, indent=4)

def JsonToHSVRange(json_str: str) -> HSVRange:
    json_dict = json.loads(json_str)
    return HSVRange(json_dict["minHSV"], json_dict["maxHSV"])

def HSVRangeListToJson(hsvRanges: List[HSVRange]) -> str:
    return json.dumps([json.loads(HSVRangeToJson(r)) for r in hsvRanges])

def JsonToHSVRangeList(json_str: str) -> List[HSVRange]:
    json_list = json.loads(json_str)
    return [JsonToHSVRange(json.dumps(o)) for o in json_list]

def TankToJson(tank: TankProcessing) -> str:
    return json.dumps({
        "min": tank.min,
        "max": tank.max,
        "hsvRanges": json.loads(HSVRangeListToJson(tank.hsvRanges)),
        "erosion_size": tank.erosion_size,
        "dilation_size": tank.dilation_size,
        "min_contour_area": tank.min_contour_area
    }, indent=4)

def JsonToTank(json_str: str) -> TankProcessing:
    json_dict = json.loads(json_str)
    return TankProcessing(json_dict["min"], json_dict["max"], JsonToHSVRangeList(json.dumps(json_dict["hsvRanges"])), json_dict["erosion_size"], json_dict["dilation_size"], json_dict["min_contour_area"])

def WriteTankSettings(tank1: TankProcessing, tank2: TankProcessing, tank3: TankProcessing):
    with open("../out/video_tank_settings.json", "w") as f:
        f.write(json.dumps([
            json.loads(TankToJson(tank1)), 
            json.loads(TankToJson(tank2)), 
            json.loads(TankToJson(tank3))
        ], indent=4))

def ReadTankSettings() -> Tuple[TankProcessing, TankProcessing, TankProcessing]:
    with open("../out/video_tank_settings.json", "r") as f:
        json_list = json.loads(f.read())
        return JsonToTank(json.dumps(json_list[0])), JsonToTank(json.dumps(json_list[1])), JsonToTank(json.dumps(json_list[2]))

# Video Markers ------------------------
def ReadVideoMarkers() -> List[int]:
    with open("../out/video_markers.json", "r") as f:
        json_str = f.read()
        return json.loads(json_str)

def WriteVideoMarkers(markers: List[int]):
    with open("../out/video_markers.json", "w") as f:
        f.write(json.dumps(markers))
    
def ToggleVideoMarker(markers: List[int], frame: int):
    if frame in markers:
        markers.remove(frame)
    else:
        markers.append(frame)
    markers.sort()

# CSV Output ------------------------
def PxToHeight(y: int, miny: int, maxy: int, L: float) -> float:
    if y == 0:
        return 0
    
    return L*(1 - (y - miny)/(maxy - miny))            

def CalculateRow(raw_frame, frame_i: int, start_frame: int, fps: int, slice_count: int, L: float, scale_percent: float, tank1: TankProcessing, tank2: TankProcessing, tank3: TankProcessing):
    # resize frame
    width = int(raw_frame.shape[1] * scale_percent / 100)
    height = int(raw_frame.shape[0] * scale_percent / 100)
    resized_frame = cv2.resize(raw_frame, (width, height))

    # convert frame to HSV
    hsv_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2HSV)
    
    tank1_min, tank1_max = tank1.getMinMax(hsv_frame.shape)
    tank2_min, tank2_max = tank2.getMinMax(hsv_frame.shape)
    tank3_min, tank3_max = tank3.getMinMax(hsv_frame.shape)

    row = [frame_i, (frame_i-start_frame)/fps]
    for slice_i in range(slice_count):
        tank1_slice_min, tank1_slice_max = tank1.getBounds(hsv_frame, slice_i, slice_count)
        tank2_slice_min, tank2_slice_max = tank2.getBounds(hsv_frame, slice_i, slice_count)
        tank3_slice_min, tank3_slice_max = tank3.getBounds(hsv_frame, slice_i, slice_count)

        tank1_slice_top    = PxToHeight(tank1_slice_min[1], tank1_min[1], tank1_max[1], L)
        tank1_slice_bottom = PxToHeight(tank1_slice_max[1], tank1_min[1], tank1_max[1], L)
        
        tank2_slice_top    = PxToHeight(tank2_slice_min[1], tank2_min[1], tank2_max[1], L)
        tank2_slice_bottom = PxToHeight(tank2_slice_max[1], tank2_min[1], tank2_max[1], L)
        
        tank3_slice_top    = PxToHeight(tank3_slice_min[1], tank3_min[1], tank3_max[1], L)
        tank3_slice_bottom = PxToHeight(tank3_slice_max[1], tank3_min[1], tank3_max[1], L)
        
        row += [
            tank1_slice_bottom, tank1_slice_top,
            tank2_slice_bottom, tank2_slice_top,
            tank3_slice_bottom, tank3_slice_top,
        ]
    
    return row