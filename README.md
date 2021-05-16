# CAN-RGX

# /data
Data goes here, currently contains `ExperimentVideo.mp4`, `FlightData.csv` & the folder `7_24_15_19_30`

Grab `data/ExperimentVideo.mp4` from `July 23 Flight Videos/Unwarped/ExperimentVideo.mp4` on the google drive

# /arduino
Code that runs on the arduino in the experiment

# /laptop
Code that runs on the laptop connected to the experiment  
  
Uses [sokol](https://github.com/floooh/sokol) for platform abstraction, [imgui](https://github.com/ocornut/imgui) (& [imgui_plot](https://github.com/soulthreads/imgui-plot)) for UI, [nlohmann::json](https://github.com/nlohmann/json) for json parsing (used for settings)

## Known but unsolved/hard to repro issues
 - Sometimes opening graphs crashes the program (an assert in sokol fires), could not reproduce. Happened like twice
 - Sometimes using the keybinds to change modes doesn't successfully send the new pump speeds (sometimes it was giving incorrect checksum errors on the arduino side, maybe some weird windows stuff with writing to serial). Pretty easy to trigger if you try for a bit. Unconfirmed if you can trigger this by clicking the button with your mouse, I couldn't manage to trigger it this way
 - **Maybe hardware** The sliced 80Hz load cell amp board doesnt work, just returns a constant value and doesnt change
 - **Almost 100% hardware** one of the flow meters gives garbage
 - **Almost 100% hardware** one of the accelerometers on one of the tanks gives garbage

# /loadcell
# /video