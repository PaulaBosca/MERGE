import cv2
from video_processing import *
import numpy as np
from typing import Tuple

def DrawTankOverlay(tank: TankProcessing, frame):
    # Get bounds in pixel coordinates
    minp, maxp = tank.getMinMax(frame.shape)

    # Draw bounds
    cv2.rectangle(frame, minp, maxp, (255, 255, 255))
    
    # Draw center line
    # r_0x = int((minp[0] + maxp[0]) / 2)
    # cv2.line(frame, (r_0x, maxp[1]), (r_0x, int(0.5*maxp[1] + 0.5*minp[1])), (255, 255, 255))
    
    # Draw labels 
    # cv2.putText(frame, "0",  (maxp[0] + 5, maxp[1] + 5), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255))
    # cv2.putText(frame, "L",  (maxp[0] + 5, minp[1] + 5), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255))
    # cv2.putText(frame, "-r", (minp[0] - 5, maxp[1] + 20), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255))
    # cv2.putText(frame, "0",  (r_0x    - 5, maxp[1] + 20), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255))
    # cv2.putText(frame, "r",  (maxp[0] - 5, maxp[1] + 20), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255))

if __name__ == "__main__":
    video = cv2.VideoCapture(abspath(join(dirname(__file__),'../data/ExperimentVideo.mp4')))
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = video.get(cv2.CAP_PROP_FPS)
    
    _mouse_x = 0
    _mouse_y = 0
    _mouse_down = False

    def onMouse(event, x, y, flags, param):
        global _mouse_x
        global _mouse_y
        global _mouse_down
        
        if event == cv2.EVENT_LBUTTONDOWN:
            _mouse_down = True
        elif event == cv2.EVENT_LBUTTONUP:
            _mouse_down = False
        
        _mouse_x = x
        _mouse_y = y

    cv2.namedWindow("MERGE Annotator")
    cv2.setMouseCallback("MERGE Annotator", onMouse)

    scale_percent = 50
    L = 16.192 # cm

    tank1, tank2, tank3 = ReadTankSettings()
    markers = ReadVideoMarkers()

    # Different ui modes
    UI_NONE = "None"
    UI_TANK1_BOUNDS = "Tank 1 Bounds"
    UI_TANK2_BOUNDS = "Tank 2 Bounds"
    UI_TANK3_BOUNDS = "Tank 3 Bounds"
    UI_TANK1_HSV = "Tank 1 HSV"
    UI_TANK2_HSV = "Tank 2 HSV"
    UI_TANK3_HSV = "Tank 3 HSV"

    was_mouse_down = False
    last_mouse_x = 0
    last_mouse_y = 0

    ui_mode = UI_NONE
    currentRangeIndex = 0
    show_masked = False
    selected_slider = 0
    slice_count = 7
    lastHSV = [0, 0, 0]

    curr_frame = 0
    auto_play = False
    auto_play_speed = 1 # frames to advance per loop when autoplaying
    while True:
        mouse_down = _mouse_down
        mouse_x = _mouse_x
        mouse_y = _mouse_y

        # Mouse click handling
        mouse_released = was_mouse_down and (not mouse_down)
        mouse_clicked = (not was_mouse_down) and mouse_down
        
        def DrawRangeSlider(frame, minx: int, maxx: int, y: int, val1: int, val2: int, minval: int, maxval: int, sliderid: int) -> Tuple[int, int]:
            cv2.line(frame, (minx, y), (maxx, y), (255, 255, 255))
            HANDLE_RADIUS = 7
            global selected_slider

            cursor_val = ((maxval - minval) / (maxx - minx)) * (mouse_x - minx)

            # Logic for min val slider
            t1 = (val1 - minval) / (maxval - minval)
            x1 = int(t1 * (maxx - minx) + minx)
            hot1 = (mouse_x - x1)**2 + (mouse_y - y)**2 <= HANDLE_RADIUS**2
            cv2.circle(frame, (x1, y), HANDLE_RADIUS, (0, 0, 255) if hot1 else (255, 255, 255), cv2.FILLED)

            if mouse_clicked and hot1:
                selected_slider = sliderid

            if mouse_down and (selected_slider == sliderid):
                val1 = cursor_val

            # Logic for max val slider
            t2 = (val2 - minval) / (maxval - minval)
            x2 = int(t2 * (maxx - minx) + minx)
            hot2 = (mouse_x - x2)**2 + (mouse_y - y)**2 <= HANDLE_RADIUS**2
            cv2.circle(frame, (x2, y), HANDLE_RADIUS, (0, 0, 255) if hot2 else (255, 255, 255), cv2.FILLED)

            if mouse_clicked and hot2:
                selected_slider = sliderid + 1

            if mouse_down and (selected_slider == sliderid + 1):
                val2 = cursor_val

            # Release cursor if mouse not down
            if not mouse_down:
                selected_slider = 0

            # Clamp values
            if minval > val1:
                val1 = minval
            elif val1 > maxval:
                val1 = maxval

            if minval > val2:
                val2 = minval
            elif val2 > maxval:
                val2 = maxval

            return int(val1), int(val2)

        def DrawTankHSVSliders(frame, tank: TankProcessing, slideridbase: int):
            width = frame.shape[1]

            for i, r in enumerate(tank.hsvRanges):
                cv2.putText(frame, str(r), (5, 200 + 40*i), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255))

            if(currentRangeIndex < len(tank.hsvRanges)):
                hsvRange = tank.hsvRanges[currentRangeIndex]

                cv2.putText(frame, "H: " + str(hsvRange.minHSV[0]) + " to " + str(hsvRange.maxHSV[0]), (300, 48), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255))
                minHSV0, maxHSV0 = DrawRangeSlider(to_display, 500, width - 50, 40, hsvRange.minHSV[0], hsvRange.maxHSV[0], 0, 255, slideridbase + 0)
                
                cv2.putText(frame, "S: " + str(hsvRange.minHSV[1]) + " to " + str(hsvRange.maxHSV[1]), (300, 88), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255))
                minHSV1, maxHSV1 = DrawRangeSlider(to_display, 500, width - 50, 80, hsvRange.minHSV[1], hsvRange.maxHSV[1], 0, 255, slideridbase + 2)
                
                cv2.putText(frame, "V: " + str(hsvRange.minHSV[2]) + " to " + str(hsvRange.maxHSV[2]), (300, 128), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255))
                minHSV2, maxHSV2 = DrawRangeSlider(to_display, 500, width - 50, 120, hsvRange.minHSV[2], hsvRange.maxHSV[2], 0, 255, slideridbase + 4)

                hsvRange.minHSV = (minHSV0, minHSV1, minHSV2)
                hsvRange.maxHSV = (maxHSV0, maxHSV1, maxHSV2)

        # Get curr frame
        video.set(cv2.CAP_PROP_POS_FRAMES, curr_frame)
        _, raw_frame = video.read()
        
        # Find starting marked frame for this section
        start_frame = markers[0]
        for marked_frame in markers:
            if marked_frame <= curr_frame:
                start_frame = marked_frame

        # Resize frame
        width = int(raw_frame.shape[1] * scale_percent / 100)
        height = int(raw_frame.shape[0] * scale_percent / 100)
        resized_frame = cv2.resize(raw_frame, (width, height))

        hsv_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2HSV)

        # Choose what to display
        if show_masked:
            tank1_mask = tank1.getMask(hsv_frame)
            tank2_mask = tank2.getMask(hsv_frame)
            tank3_mask = tank3.getMask(hsv_frame)

            all_masks = tank1_mask + tank2_mask + tank3_mask
            to_display = cv2.merge([all_masks, all_masks, all_masks]) 
        else:
            to_display = resized_frame

        # Overlay
        cv2.putText(to_display, f"Frame {curr_frame}/{frame_count - 1} Section @ {start_frame}: {curr_frame - start_frame}, {round((curr_frame-start_frame)/fps, 2)}s", (5, 20), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255))
        cv2.putText(to_display, "Autoplay (" + ("Enabled" if auto_play else "Disabled") + "): " + str(auto_play_speed), (5, 40), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255))
        cv2.putText(to_display, f"UI Mode: {ui_mode}", (5, 60), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255))
        cv2.putText(to_display, f"Slices: {slice_count}", (5, 80), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255))
        cv2.putText(to_display, f"Last HSV: {lastHSV}", (5, 100), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255))

        if curr_frame in markers:
            cv2.putText(to_display, "Marked Frame", (5, 120), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255))

        tank1_min, tank1_max = tank1.getMinMax(to_display.shape)
        tank2_min, tank2_max = tank2.getMinMax(to_display.shape)
        tank3_min, tank3_max = tank3.getMinMax(to_display.shape)

        cv2.rectangle(to_display, tank1_min, tank1_max, (255, 255, 255))
        cv2.rectangle(to_display, tank2_min, tank2_max, (255, 255, 255))
        cv2.rectangle(to_display, tank3_min, tank3_max, (255, 255, 255))
        
        if mouse_clicked:
            lastHSV = hsv_frame[mouse_y, mouse_x]

        for i in range(slice_count):
            boundsmin, boundsmax = tank1.getBounds(hsv_frame, slice_i=i, slice_count=slice_count)
            cv2.rectangle(to_display, boundsmin, boundsmax, (255, 255, 255))
            
            boundsmin, boundsmax = tank2.getBounds(hsv_frame, slice_i=i, slice_count=slice_count)
            cv2.rectangle(to_display, boundsmin, boundsmax, (255, 255, 255))

            boundsmin, boundsmax = tank3.getBounds(hsv_frame, slice_i=i, slice_count=slice_count)
            cv2.rectangle(to_display, boundsmin, boundsmax, (255, 255, 255))

        # Handle different ui modes
        if ui_mode == UI_TANK1_BOUNDS:
            if mouse_clicked:
                tank1.min = (mouse_x / width, mouse_y / height)
            if mouse_down:
                tank1.max = (mouse_x / width, mouse_y / height)      
        elif ui_mode == UI_TANK2_BOUNDS:
            if mouse_clicked:
                tank2.min = (mouse_x / width, mouse_y / height)
            if mouse_down:
                tank2.max = (mouse_x / width, mouse_y / height)
        elif ui_mode == UI_TANK3_BOUNDS:
            if mouse_clicked:
                tank3.min = (mouse_x / width, mouse_y / height)
            if mouse_down:
                tank3.max = (mouse_x / width, mouse_y / height)
        elif ui_mode == UI_TANK1_HSV:
            DrawTankHSVSliders(to_display, tank1, 1)
        elif ui_mode == UI_TANK2_HSV:
            DrawTankHSVSliders(to_display, tank2, 7)
        elif ui_mode == UI_TANK3_HSV:
            DrawTankHSVSliders(to_display, tank3, 13)

        # Show frame
        cv2.imshow("MERGE Annotator", to_display)    

        # Handle key input
        key = cv2.waitKeyEx(1)
        if (key == 113) or (key == 81) or (key == 27): # q or Q or escape - Quit
            break
        elif key == 2424832: # left arrow - Previous frame
            if curr_frame > 0:
                curr_frame = curr_frame - 1
        elif key == 2555904: # right arrow - Next frame
            if curr_frame < (frame_count - 1):
                curr_frame = curr_frame + 1
        elif key == 44: # ',' key - Previous marked frame
            prev_marked_frame = markers[0]
            for marker in markers:
                if marker < curr_frame:
                    prev_marked_frame = marker

            if prev_marked_frame < frame_count:
                curr_frame = prev_marked_frame
        elif key == 46: # ',' key - Next marked frame
            next_marked_frame = markers[0]
            for marker in reversed(markers):
                if marker > curr_frame:
                    next_marked_frame = marker

            if next_marked_frame < frame_count:
                curr_frame = next_marked_frame
        elif key == 32: # space - Toggle autoplay
            auto_play = not auto_play
        elif key == 2490368: # up arrow - Increase autoplay speed
            auto_play_speed = auto_play_speed + 1
        elif key == 2621440: # down arrow - Decrease autoplay speed
            auto_play_speed = auto_play_speed - 1
        elif key == 49: # 1 key - switch to changing tank 1 bounds, clicking again toggles
            ui_mode = UI_NONE if (ui_mode == UI_TANK1_BOUNDS) else UI_TANK1_BOUNDS 
        elif key == 50: # 2 key - switch to changing tank 2 bounds, clicking again toggles
            ui_mode = UI_NONE if (ui_mode == UI_TANK2_BOUNDS) else UI_TANK2_BOUNDS
        elif key == 51: # 3 key - switch to changing tank 3 bounds, clicking again toggles
            ui_mode = UI_NONE if (ui_mode == UI_TANK3_BOUNDS) else UI_TANK3_BOUNDS
        
        elif key == 52: # 4 key - switch to changing tank 1 HSV, clicking again scrolls through the ranges
            if (ui_mode == UI_TANK1_HSV) and (len(tank1.hsvRanges) > 0):
                currentRangeIndex = (currentRangeIndex + 1) % len(tank1.hsvRanges)
            else:
                ui_mode = UI_TANK1_HSV
                currentRangeIndex = 0
        elif key == 53: # 5 key - switch to changing tank 2 HSV, clicking again scrolls through the ranges
            if (ui_mode == UI_TANK2_HSV) and (len(tank2.hsvRanges) > 0):
                currentRangeIndex = (currentRangeIndex + 1) % len(tank2.hsvRanges)
            else:
                ui_mode = UI_TANK2_HSV
                currentRangeIndex = 0
        elif key == 54: # 6 key - switch to changing tank 3 HSV, clicking again scrolls through the ranges
            if (ui_mode == UI_TANK3_HSV) and (len(tank3.hsvRanges) > 0):
                currentRangeIndex = (currentRangeIndex + 1) % len(tank3.hsvRanges)
            else:
                ui_mode = UI_TANK3_HSV
                currentRangeIndex = 0

        elif key == 45: # - and _ key - removes the current hsv range 
            if (ui_mode == UI_TANK1_HSV) and (currentRangeIndex < len(tank1.hsvRanges)):
                del tank1.hsvRanges[currentRangeIndex]
                if len(tank1.hsvRanges) > 0:
                    currentRangeIndex = currentRangeIndex % len(tank1.hsvRanges)
            elif (ui_mode == UI_TANK2_HSV) and (currentRangeIndex < len(tank2.hsvRanges)):
                del tank2.hsvRanges[currentRangeIndex]
                if len(tank2.hsvRanges) > 0:
                    currentRangeIndex = currentRangeIndex % len(tank2.hsvRanges)
            elif (ui_mode == UI_TANK3_HSV) and (currentRangeIndex < len(tank3.hsvRanges)):
                del tank3.hsvRanges[currentRangeIndex]
                if len(tank3.hsvRanges) > 0:
                    currentRangeIndex = currentRangeIndex % len(tank3.hsvRanges)
        elif key == 61: # = and + key - adds an hsv range to the current tank 
            if ui_mode == UI_TANK1_HSV:
                tank1.hsvRanges.append(HSVRange( (0, 0, 0), (0, 0, 0) ))
            elif ui_mode == UI_TANK2_HSV:
                tank2.hsvRanges.append(HSVRange( (0, 0, 0), (0, 0, 0) ))
            elif ui_mode == UI_TANK3_HSV:
                tank3.hsvRanges.append(HSVRange( (0, 0, 0), (0, 0, 0) ))

        elif key == 13: # enter key - records a run start/end
            ToggleVideoMarker(markers, curr_frame)
        elif key == 115: # s key - saves the tank settings and markers
            WriteTankSettings(tank1, tank2, tank3)
            WriteVideoMarkers(markers)
        elif key == 106: # j key - allows you to type a frame number into the console to jump there
            jumpFrame = int(input("Enter frame #:"))
            if (0 <= jumpFrame) and (jumpFrame < frame_count):
                curr_frame = jumpFrame
        elif key == 112: # p key - prints csv row from current frame
            print(CalculateRow(raw_frame, curr_frame, start_frame, fps, slice_count, L, scale_percent, tank1, tank2, tank3))
        elif key == 122: # z key - allows you to set the zoom scaling (range 1 to 100)
            scale = int(input("Enter scale [1, 100]:"))
            if (1 <= scale) and (scale <= 100):
                scale_percent = scale
        elif key == 109: # m key - toggles between color and mask view
            show_masked = not show_masked
        elif key == 91: # [ key - lowers the amount of slices
            if slice_count > 1:
                slice_count = slice_count - 1
        elif key == 93: # ] key - increases the amount of slices
            slice_count = slice_count + 1
        elif key != -1:
            print(key)

        # Advance frame if autoplay
        if auto_play:
            new_frame = curr_frame + auto_play_speed
            if (0 <= new_frame) and (new_frame < frame_count):
                curr_frame = new_frame

        # Update last mouse state
        was_mouse_down = mouse_down
        last_mouse_x = mouse_x
        last_mouse_y = mouse_y 