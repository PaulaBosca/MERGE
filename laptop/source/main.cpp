#define SOKOL_GLCORE33
#define SOKOL_IMPL
#define SOKOL_IMGUI_IMPL
#define SOKOL_VALIDATE_NON_FATAL

#include "lib/imgui/imgui.cpp"
#include "lib/imgui/imgui_draw.cpp"
#include "lib/imgui/imgui_widgets.cpp"
#include "lib/imgui/imgui_plot.cpp"

#include "lib/sokol/sokol_app.h"
#include "lib/sokol/sokol_gfx.h"
#include "lib/sokol/sokol_time.h"
#include "lib/imgui/imgui.h"
#include "lib/imgui/imgui_plot.h"
#include "lib/sokol/sokol_imgui.h"

#include <windows.h>
#include "lib/json.hpp"

#include <stdio.h>
#include <string.h>
#include <vector>
#include <chrono>

#include "merge_protocol.h"
#include "merge_packets.h"

#define ArraySize(array) (sizeof(array)/sizeof(array[0]))
#define FLT32_MAX 3.402823e+38

//Currently loaded settings
struct StateSettings {
   char *name;

   float time;
   float pump1; // Pump 1 percent, from -100 to 100
   float pump2; // Pump 2 percent, from -100 to 100
   char keybind;

   int run_count;
};

uint32_t COM_port_number = 0;
std::vector<StateSettings> states;
StateSettings *selected_state = NULL;
StateSettings *current_state = NULL;
int side_list_width = 300;
int graph_height = 300;
float loadcell_offsets[6] = {};
float loadcell_sensitivities[6] = {1, 1, 1, 1, 1, 1};
float accel_offsets[4] = {};
float accel_sensitivities[4] = {1, 1, 1, 1};
float flow_threshold = 0;

float return_to_idle_time = 0;

//Loads settings.json
void ReadSettings() {
    //Read text from file, do nothing if file doesnt exist
    FILE *settings_file = fopen("settings.json", "rb");
    if (settings_file == NULL) return;

    fseek(settings_file, 0, SEEK_END);
    int file_size = ftell(settings_file);
    fseek(settings_file, 0, SEEK_SET);
    
    char *settings_json = (char *)malloc(file_size + 1);
    fread(settings_json, file_size, 1, settings_file);
    settings_json[file_size] = '\0';
    fclose(settings_file);

    //Parse json & update settings
    nlohmann::json settings = nlohmann::json::parse(settings_json, nullptr, false);
    if(settings.is_discarded()) {
        MessageBoxA(NULL, "Invalid settings.json file", "Error", MB_ICONEXCLAMATION);
        exit(0);
    }

    if(settings["port"].is_number()) COM_port_number = settings["port"].get<uint32_t>();
    if(settings["side_list_width"].is_number()) side_list_width = settings["side_list_width"].get<int>();
    if(settings["graph_height"].is_number()) graph_height = settings["graph_height"].get<int>();
    if(settings["flow_threshold"].is_number()) flow_threshold = settings["flow_threshold"].get<float>();

    //Load loadcell calibration constants 
    for(int i = 0; i < 6; i++) {
        char object_name[12];
        snprintf(object_name, ArraySize(object_name), "loadcell%d", i + 1);

        if(settings[object_name]["offset"].is_number()) loadcell_offsets[i] = settings[object_name]["offset"].get<float>();
        if(settings[object_name]["sensitivity"].is_number()) loadcell_sensitivities[i] = settings[object_name]["sensitivity"].get<float>();
    }

    //Load accelerometer calibration constants 
    if(settings["accel_fixed"]["offset"].is_number()) accel_offsets[0] = settings["accel_fixed"]["offset"].get<float>();
    if(settings["accel_fixed"]["sensitivity"].is_number()) accel_sensitivities[0] = settings["accel_fixed"]["sensitivity"].get<float>();

    if(settings["accel_tank1"]["offset"].is_number()) accel_offsets[1] = settings["accel_tank1"]["offset"].get<float>();
    if(settings["accel_tank1"]["sensitivity"].is_number()) accel_sensitivities[1] = settings["accel_tank1"]["sensitivity"].get<float>();

    if(settings["accel_tank2"]["offset"].is_number()) accel_offsets[2] = settings["accel_tank2"]["offset"].get<float>();
    if(settings["accel_tank2"]["sensitivity"].is_number()) accel_sensitivities[2] = settings["accel_tank2"]["sensitivity"].get<float>();

    if(settings["accel_tank3"]["offset"].is_number()) accel_offsets[3] = settings["accel_tank3"]["offset"].get<float>();
    if(settings["accel_tank3"]["sensitivity"].is_number()) accel_sensitivities[3] = settings["accel_tank3"]["sensitivity"].get<float>();

    //Free & clear states array
    current_state = NULL;
    selected_state = NULL;
    for(int i = 0; i < states.size(); i++) {
        free(states[i].name);
    }
    states.clear();

    //Load new states from settings
    for(nlohmann::json::iterator it = settings["states"].begin(); it != settings["states"].end(); ++it) {
        StateSettings new_state = {};
        
        std::string name_string = (*it)["name"].get<std::string>();
        new_state.name = (char *)malloc(name_string.length() + 1);
        memcpy(new_state.name, name_string.c_str(), name_string.length() + 1);

        new_state.time = (*it)["time"].get<float>();
        new_state.pump1 = (*it)["pump1"].get<float>();
        new_state.pump2 = (*it)["pump2"].get<float>();
        
        std::string keybind_string = (*it)["keybind"].get<std::string>();
        new_state.keybind = (keybind_string.length() == 1) ? keybind_string[0] : '\0'; 
        
        states.push_back(new_state);
    }

    free(settings_json);
}

#define GRAPH_SAMPLE_COUNT 1024
struct GraphData {
    const char *name;
    float vals[GRAPH_SAMPLE_COUNT];
    float ts[GRAPH_SAMPLE_COUNT];
    int i;
    int count;
};

void WriteSample(GraphData *graph, float t, float val) {
    graph->vals[graph->i] = val;
    graph->ts[graph->i] = t;
    
    graph->i++;
    if(graph->i == GRAPH_SAMPLE_COUNT) graph->i = 0;
    if(graph->count < GRAPH_SAMPLE_COUNT) graph->count++;
}

//Define graphs here
GraphData loadcell1 = { "Loadcell 1" };
GraphData loadcell2 = { "Loadcell 2" };
GraphData loadcell3 = { "Loadcell 3" };
GraphData loadcell4 = { "Loadcell 4" };
GraphData loadcell5 = { "Loadcell 5" };
GraphData loadcell6 = { "Loadcell 6" };

GraphData accel_fixed_x = { "Fixed Accel X" };
GraphData accel_fixed_y = { "Fixed Accel Y" };
GraphData accel_fixed_z = { "Fixed Accel Z" };

GraphData accel_tank1_x = { "Tank 1 Accel X" };
GraphData accel_tank1_y = { "Tank 1 Accel Y" };
GraphData accel_tank1_z = { "Tank 1 Accel Z" };

GraphData accel_tank2_x = { "Tank 2 Accel X" };
GraphData accel_tank2_y = { "Tank 2 Accel Y" };
GraphData accel_tank2_z = { "Tank 2 Accel Z" };

GraphData accel_tank3_x = { "Tank 3 Accel X" };
GraphData accel_tank3_y = { "Tank 3 Accel Y" };
GraphData accel_tank3_z = { "Tank 3 Accel Z" };

GraphData flow_sensor1 = { "Flow Sensor 1" };
GraphData flow_sensor2 = { "Flow Sensor 2" };
GraphData flow_sensor3 = { "Flow Sensor 3" };

GraphData *graphs[] = {
    &loadcell1,
    &loadcell2,
    &loadcell3,
    &loadcell4,
    &loadcell5,
    &loadcell6,

    &accel_fixed_x,
    &accel_fixed_y,
    &accel_fixed_z,
    
    &accel_tank1_x,
    &accel_tank1_y,
    &accel_tank1_z,
    
    &accel_tank2_x,
    &accel_tank2_y,
    &accel_tank2_z,

    &accel_tank3_x,
    &accel_tank3_y,
    &accel_tank3_z,

    &flow_sensor1,
    &flow_sensor2,
    &flow_sensor3,
};

HANDLE com_handle = INVALID_HANDLE_VALUE;
FILE *csv_file = NULL; 

bool IsConnectedComms() {
    return com_handle != INVALID_HANDLE_VALUE;
}

void DisconnectComms() {
    //already disconnected, return
    if(com_handle == INVALID_HANDLE_VALUE) return;

    //close com handle and set to invalid handle
    CloseHandle(com_handle);
    com_handle = INVALID_HANDLE_VALUE;

    //close csv file handle and set to NULL
    fclose(csv_file);
    csv_file = NULL;
}

void AttemptConnectComms() {
    //already connected, return
    if(com_handle != INVALID_HANDLE_VALUE) return;

    char com_port_name[20];
    snprintf(com_port_name, 20, "\\\\.\\COM%d", COM_port_number);
    
    HANDLE new_com_handle = CreateFile(com_port_name, GENERIC_READ | GENERIC_WRITE, 0,
                                        NULL, OPEN_EXISTING, 0, NULL);

    //failed to open handle, return                                    
    if(new_com_handle == INVALID_HANDLE_VALUE) return;

    DCB serial_params = {};
    serial_params.DCBlength = sizeof(serial_params);
    GetCommState(new_com_handle, &serial_params);

    serial_params.BaudRate = CBR_115200;
    serial_params.ByteSize = 8;
    serial_params.StopBits = ONESTOPBIT;
    serial_params.Parity = NOPARITY;
    serial_params.fDtrControl = DTR_CONTROL_ENABLE;
    
    if(!SetCommState(new_com_handle, &serial_params)) {
        //Setting COM settings failed, close handle and return
        CloseHandle(new_com_handle);
        return;
    }

    SYSTEMTIME run_start_time = {};
    GetLocalTime(&run_start_time);

    char csv_file_name[100];
    snprintf(csv_file_name, 100, "%hu_%hu_%hu_%hu_%hu.csv", 
             run_start_time.wMonth, run_start_time.wDay, run_start_time.wHour,
             run_start_time.wMinute, run_start_time.wSecond);

    FILE *new_csv_file = fopen(csv_file_name, "wb");
    if(new_csv_file == NULL) {
        //Creating CSV file failed, close com handle and return
        CloseHandle(new_com_handle);
        return;
    }

    fprintf(new_csv_file, "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n",
        "Time", "State",
        "Loadcell 1", "Loadcell 2",
        "Loadcell 3", "Loadcell 4",
        "Loadcell 5", "Loadcell 6",
        "Fixed Accel X", "Fixed Accel Y", "Fixed Accel Z",
        "Tank 1 Accel X", "Tank 1 Accel Y", "Tank 1 Accel Z",
        "Tank 2 Accel X", "Tank 2 Accel Y", "Tank 2 Accel Z",
        "Tank 3 Accel X", "Tank 3 Accel Y", "Tank 3 Accel Z",
        "Flow Sensor 1", "Flow Sensor 2", "Flow Sensor 3");

    //Connection successful, settings applied & csv created, now connected
    com_handle = new_com_handle;
    csv_file = new_csv_file;

    OutputDebugStringA("Connected\n");
}

void HandlePacket(MERGEPacket packet);

void HandleComms() {
    //Not connected, return
    if(com_handle == INVALID_HANDLE_VALUE) return;

    bool has_data = true;
    while(has_data) {
        DWORD dwErrorFlags;
        COMSTAT ComStat;
        if(!ClearCommError(com_handle, &dwErrorFlags, &ComStat)) {
            //Some error with the com handle, disconnect and return
            DisconnectComms();
            return;
        }
        
        uint32_t bytesAvailable = (uint32_t)ComStat.cbInQue;

        uint8_t buffer[1024];
        DWORD bytes_read = 0;
        if(!ReadFile(com_handle, buffer, (bytesAvailable > ArraySize(buffer)) ? ArraySize(buffer) : bytesAvailable, &bytes_read, NULL)) {
            //Read failed, disconnect and return
            DisconnectComms();
            return;
        }

        has_data = (bytes_read != 0);

        for(int i = 0; i < bytes_read; i++) {
            MERGEPacket packet;
            if(recvPacket(&packet, buffer[i])) HandlePacket(packet);
        }
    }
}

uint64_t getEpochMillis() {
    return (uint64_t)std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now().time_since_epoch()).count();
}

uint64_t last_pump_time = 0; // last time a pump packet was sent
void SendPumpVals() {
    if(com_handle == INVALID_HANDLE_VALUE) return;
    
    float pump1_percent = 0;
    float pump2_percent = 0;
    
    if(current_state != NULL) {
        pump1_percent = current_state->pump1;
        pump2_percent = current_state->pump2;
    }

    PumpPacket packet = {};
    packet.pump1 = (pump1_percent + 100.0f) / 200.0f;
    packet.pump2 = (pump2_percent + 100.0f) / 200.0f;

    sendPacket((uint8_t *)&packet, sizeof(packet), PumpPacketID, com_handle);
    last_pump_time = getEpochMillis();
}

void HandlePacket(MERGEPacket packet) {
    if(packet.type == PrintPacketID) {
        char print_buf[100];
        snprintf(print_buf, 100, "Print Msg: '%.*s'\n", packet.len, (char *)packet.payload);
        OutputDebugStringA(print_buf);
    } else if((packet.type == DataPacketID) && (packet.len == sizeof(DataPacket))) {
        DataPacket *data_packet = (DataPacket *)packet.payload;
        
        for(int i = 0; i < 6; i++) {
            data_packet->loadcell[i] = loadcell_sensitivities[i]*data_packet->loadcell[i] + loadcell_offsets[i];
        }

        data_packet->accel_fixed_x = accel_sensitivities[0]*data_packet->accel_fixed_x + accel_offsets[0];
        data_packet->accel_fixed_y = accel_sensitivities[0]*data_packet->accel_fixed_y + accel_offsets[0];
        data_packet->accel_fixed_z = accel_sensitivities[0]*data_packet->accel_fixed_z + accel_offsets[0];

        data_packet->accel_tank1_x = accel_sensitivities[1]*data_packet->accel_tank1_x + accel_offsets[1];
        data_packet->accel_tank1_y = accel_sensitivities[1]*data_packet->accel_tank1_y + accel_offsets[1];
        data_packet->accel_tank1_z = accel_sensitivities[1]*data_packet->accel_tank1_z + accel_offsets[1];

        data_packet->accel_tank2_x = accel_sensitivities[2]*data_packet->accel_tank2_x + accel_offsets[2];
        data_packet->accel_tank2_y = accel_sensitivities[2]*data_packet->accel_tank2_y + accel_offsets[2];
        data_packet->accel_tank2_z = accel_sensitivities[2]*data_packet->accel_tank2_z + accel_offsets[2];

        data_packet->accel_tank3_x = accel_sensitivities[3]*data_packet->accel_tank3_x + accel_offsets[3];
        data_packet->accel_tank3_y = accel_sensitivities[3]*data_packet->accel_tank3_y + accel_offsets[3];
        data_packet->accel_tank3_z = accel_sensitivities[3]*data_packet->accel_tank3_z + accel_offsets[3];

        //write data to graphs
        WriteSample(&loadcell1, data_packet->timestamp / 1000.0, data_packet->loadcell[0]);
        WriteSample(&loadcell2, data_packet->timestamp / 1000.0, data_packet->loadcell[1]);
        WriteSample(&loadcell3, data_packet->timestamp / 1000.0, data_packet->loadcell[2]);
        WriteSample(&loadcell4, data_packet->timestamp / 1000.0, data_packet->loadcell[3]);
        WriteSample(&loadcell5, data_packet->timestamp / 1000.0, data_packet->loadcell[4]);
        WriteSample(&loadcell6, data_packet->timestamp / 1000.0, data_packet->loadcell[5]);

        WriteSample(&accel_fixed_x, data_packet->timestamp / 1000.0, data_packet->accel_fixed_x);
        WriteSample(&accel_fixed_y, data_packet->timestamp / 1000.0, data_packet->accel_fixed_y);
        WriteSample(&accel_fixed_z, data_packet->timestamp / 1000.0, data_packet->accel_fixed_z);

        WriteSample(&accel_tank1_x, data_packet->timestamp / 1000.0, data_packet->accel_tank1_x);
        WriteSample(&accel_tank1_y, data_packet->timestamp / 1000.0, data_packet->accel_tank1_y);
        WriteSample(&accel_tank1_z, data_packet->timestamp / 1000.0, data_packet->accel_tank1_z);

        WriteSample(&accel_tank2_x, data_packet->timestamp / 1000.0, data_packet->accel_tank2_x);
        WriteSample(&accel_tank2_y, data_packet->timestamp / 1000.0, data_packet->accel_tank2_y);
        WriteSample(&accel_tank2_z, data_packet->timestamp / 1000.0, data_packet->accel_tank2_z);

        WriteSample(&accel_tank3_x, data_packet->timestamp / 1000.0, data_packet->accel_tank3_x);
        WriteSample(&accel_tank3_y, data_packet->timestamp / 1000.0, data_packet->accel_tank3_y);
        WriteSample(&accel_tank3_z, data_packet->timestamp / 1000.0, data_packet->accel_tank3_z);

        WriteSample(&flow_sensor1, data_packet->timestamp / 1000.0, data_packet->flow_sensor[0]);
        WriteSample(&flow_sensor2, data_packet->timestamp / 1000.0, data_packet->flow_sensor[1]);
        WriteSample(&flow_sensor3, data_packet->timestamp / 1000.0, data_packet->flow_sensor[2]);

        //save data to csv
        fprintf(csv_file, "%llu,%s,%d,%d,%d,%d,%d,%d,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%f,%f,%f\n",
            data_packet->timestamp, current_state ? current_state->name : "Idle",
            data_packet->loadcell[0], data_packet->loadcell[1],
            data_packet->loadcell[2], data_packet->loadcell[3],
            data_packet->loadcell[4], data_packet->loadcell[5],
            data_packet->accel_fixed_x, data_packet->accel_fixed_y, data_packet->accel_fixed_z,
            data_packet->accel_tank1_x, data_packet->accel_tank1_y, data_packet->accel_tank1_z,
            data_packet->accel_tank2_x, data_packet->accel_tank2_y, data_packet->accel_tank2_z,
            data_packet->accel_tank3_x, data_packet->accel_tank3_y, data_packet->accel_tank3_z,
            data_packet->flow_sensor[0], data_packet->flow_sensor[1], data_packet->flow_sensor[2]);
    }
}

//Get last edit time for a given file
uint64_t GetFileTimestamp(const char* path) {
    FILETIME last_write_time = {};
    HANDLE file_handle = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ,
                                     NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    
    if(file_handle != INVALID_HANDLE_VALUE) {
        GetFileTime(file_handle, NULL, NULL, &last_write_time);
        CloseHandle(file_handle);
    }
    
    return (uint64_t)last_write_time.dwLowDateTime | 
          ((uint64_t)last_write_time.dwHighDateTime << 32);
}

void SetState(StateSettings *state) {
    if(state == NULL) {
        //Set state to idle
        current_state = NULL;
        return_to_idle_time = 0;
    } else {
        current_state = state;
        return_to_idle_time = state->time;
        state->run_count++;
    }

    SendPumpVals();
}

bool CheckFlowSensor(GraphData *flow_sensor) {
    if(flow_sensor->count > 0) {
        return flow_sensor->vals[(flow_sensor->i + ArraySize(flow_sensor->vals) - 1) % ArraySize(flow_sensor->vals)] > flow_threshold;
    }
    return false;
}

bool close_graphs_pending = false;
uint64_t last_settings_read_time = 0; //last change time for the settings.json file that was read
uint64_t last_time = 0; //used for frame timer
void frame() {
    //Watch settings file for changes, read if file has changed
    uint64_t settings_change_time = GetFileTimestamp("settings.json");
    if(settings_change_time > last_settings_read_time) {
        ReadSettings();
        last_settings_read_time = settings_change_time;
    }

    //send pump 
    if((getEpochMillis() - last_pump_time) >= 1000/*1 sec*/) {
        SendPumpVals();
    }

    const int width = sapp_width();
    const int height = sapp_height();
    const double delta_time = stm_sec(stm_laptime(&last_time));
    simgui_new_frame(width, height, delta_time);

    ImGuiStyle *style = &ImGui::GetStyle();
    style->WindowPadding = ImVec2(0, 0);
    style->WindowRounding = 0.0f;
    style->Colors[ImGuiCol_WindowBg] = ImVec4(0.15, 0.15, 0.15, 1);
    style->ItemSpacing = ImVec2(0, 10);

    // draw graphs window
    ImGui::SetNextWindowPos(ImVec2(0, 0), ImGuiCond_Always);
    ImGui::SetNextWindowSize(ImVec2(width - side_list_width, height), ImGuiCond_Always);    
    ImGui::Begin("GraphWindow", NULL, ImGuiWindowFlags_NoResize | ImGuiWindowFlags_NoMove |
                                      ImGuiWindowFlags_NoTitleBar | ImGuiWindowFlags_NoCollapse |
                                      ImGuiWindowFlags_NoBringToFrontOnFocus);
    
    ImGui::Text("Application average %.3f ms/frame (%.1f FPS)", 1000.0f / ImGui::GetIO().Framerate, ImGui::GetIO().Framerate);
    ImGui::Text("COM %d (%s)", COM_port_number, IsConnectedComms() ? "Connected" : "Not Connected");

    ImGui::SameLine(0.0f, 10);
    if(ImGui::Button("Reconnect")) {
        DisconnectComms();
    }

    ImGui::Text("Flow Sensors: %s %s %s",
        CheckFlowSensor(&flow_sensor1) ? "Tank 1 Filling" : "-",
        CheckFlowSensor(&flow_sensor2) ? "Tank 2 Filling" : "-",
        CheckFlowSensor(&flow_sensor3) ? "Tank 3 Filling" : "-"
    );
    
    if(current_state != NULL) {
        ImGui::Text("Current State: %s, %.2f s remaining", current_state->name, return_to_idle_time);
    }

    if(close_graphs_pending) {
        close_graphs_pending = false;

        ImGui::GetStateStorage()->SetInt(ImGui::GetID("All Load Cells"), 0);
            
        for(int i = 0; i < ArraySize(graphs); i++) {
            GraphData *graph = graphs[i];
            ImGui::GetStateStorage()->SetInt(ImGui::GetID(graph->name), 0);
        }
    }

    if(ImGui::CollapsingHeader("All Load Cells")) {
        float *lines[] = {
            loadcell1.vals, loadcell2.vals,
            loadcell3.vals, loadcell4.vals,
            loadcell5.vals, loadcell6.vals,
        };

        uint32_t colors[] = {
            0xFFFFAA00, 0xFFFFAA00,
            0xFF00FF00, 0xFF00FF00, 
            0xFF0000FF, 0xFF0000FF,  
        };

        //Find min and max vals in graph data (used for plt scale)
        float graph_max = -FLT32_MAX;
        float graph_min = FLT32_MAX;
        for(int i = 0; i < ArraySize(graphs); i++) {
            GraphData *graph = graphs[i];
            for(int j = 0; j < graph->count; j++) {
                float val = graph->vals[j];
                if(val > graph_max) graph_max = val;
                if(val < graph_min) graph_min = val;
            }
        }

        ImGui::PlotConfig conf;
        conf.values.xs = loadcell1.ts;
        conf.values.ys_list = (const float **)lines;
        conf.values.ys_count = ArraySize(lines);
        conf.values.count = loadcell1.count;
        conf.values.colors = colors;
        conf.scale.min = graph_min;
        conf.scale.max = graph_max;
        conf.tooltip.show = true;
        conf.tooltip.format = "x=%.2f, y=%.2f";
        conf.grid_x.show = false;
        conf.grid_y.show = false;
        conf.frame_size = ImVec2(width - side_list_width, graph_height);
        conf.line_thickness = 2.f;

        ImGui::Plot("All Load Cells", conf);
    }

    for(int i = 0; i < ArraySize(graphs); i++) {
        GraphData *graph = graphs[i];
        if(ImGui::CollapsingHeader(graph->name)) {
            //Find min and max vals in graph data (used for plt scale)
            float graph_max = -FLT32_MAX;
            float graph_min = FLT32_MAX;
            for(int j = 0; j < graph->count; j++) {
                float val = graph->vals[j];
                if(val > graph_max) graph_max = val;
                if(val < graph_min) graph_min = val;
            }

            ImGui::PlotConfig conf;
            conf.values.xs = graph->ts;
            conf.values.ys = graph->vals;
            conf.values.count = graph->count;
            conf.scale.min = graph_min;
            conf.scale.max = graph_max;
            conf.tooltip.show = true;
            conf.tooltip.format = "x=%.2f, y=%.2f";
            conf.grid_x.show = false;
            conf.grid_y.show = false;
            conf.frame_size = ImVec2(width - side_list_width, graph_height);
            conf.line_thickness = 2.f;

            ImGui::Plot(graph->name, conf);
        }
    }

    ImGui::End();

    // draw side list
    ImGui::SetNextWindowPos(ImVec2(width - side_list_width, 0), ImGuiCond_Always);
    ImGui::SetNextWindowSize(ImVec2(side_list_width, height), ImGuiCond_Always);    
    ImGui::Begin("SideList", NULL, ImGuiWindowFlags_NoResize | ImGuiWindowFlags_NoMove |
                                   ImGuiWindowFlags_NoTitleBar | ImGuiWindowFlags_NoCollapse |
                                   ImGuiWindowFlags_NoBringToFrontOnFocus);

    ImGui::Indent(10);
    ImGui::Dummy(ImVec2(0, 0));
    for(int i = 0; i < states.size(); i++) {
        StateSettings *state = &states[i];

        char *buttonLabel = "";
        if(state == current_state) {
            buttonLabel = " RUNNING";
        } else if(state == selected_state) {
            buttonLabel = " SELECTED";
        }

        char button_text[128];
        snprintf(button_text, 128, "%s (%c, %d runs)%s", state->name, state->keybind, state->run_count, buttonLabel);
        if(ImGui::Button(button_text, ImVec2(side_list_width - 20, 60))) {
            selected_state = state;
        }
    }
    ImGui::Unindent(10);

    ImGui::End();

    //If theres a state active, decrease return_to_idle_time and reset state if time runs out
    if(current_state != NULL) {
        return_to_idle_time -= delta_time;
        if(return_to_idle_time < 0) {
            SetState(NULL);
        }
    }

    //Will attempt to reconnect to com port if not connected
    AttemptConnectComms();

    //Process comms from the serial port
    HandleComms();

    // the sokol_gfx draw pass
    sg_pass_action pass_action = {};
    pass_action.colors[0].action = SG_ACTION_CLEAR;
    pass_action.colors[0].val[0] = 0.0f;
    pass_action.colors[0].val[1] = 0.0f;
    pass_action.colors[0].val[2] = 0.0f;
    pass_action.colors[0].val[3] = 1.0f;

    sg_begin_default_pass(&pass_action, width, height);
    simgui_render();
    sg_end_pass();
    sg_commit();
}

void init() {
    // setup sokol-gfx, sokol-time and sokol-imgui
    sg_desc desc = { };
    desc.mtl_device = sapp_metal_get_device();
    desc.mtl_renderpass_descriptor_cb = sapp_metal_get_renderpass_descriptor;
    desc.mtl_drawable_cb = sapp_metal_get_drawable;
    desc.d3d11_device = sapp_d3d11_get_device();
    desc.d3d11_device_context = sapp_d3d11_get_device_context();
    desc.d3d11_render_target_view_cb = sapp_d3d11_get_render_target_view;
    desc.d3d11_depth_stencil_view_cb = sapp_d3d11_get_depth_stencil_view;
    desc.gl_force_gles2 = sapp_gles2();
    sg_setup(&desc);
    stm_setup();

    // use sokol-imgui with all default-options (we're not doing
    // multi-sampled rendering or using non-default pixel formats)
    simgui_desc_t simgui_desc = {};
    simgui_setup(&simgui_desc);

    //Read settings on startup
    ReadSettings();
    last_settings_read_time = GetFileTimestamp("settings.json");
}

void cleanup() {
    simgui_shutdown();
    sg_shutdown();
}

void input(const sapp_event* event) {
    simgui_handle_event(event);

    if(event->type == SAPP_EVENTTYPE_KEY_UP) {
        //NOTE: event->key_code returns a keycode, not a character, but the letter keycodes 
        //      match the ascii codes of the capital letters & other characters (eg. space, period ...)
                
        if(event->key_code == ' ') {
            SetState(selected_state);
            selected_state = NULL;
        } else if(event->key_code == SAPP_KEYCODE_BACKSPACE) {
            close_graphs_pending = true;
        } else {
            for(int i = 0; i < states.size(); i++) {
                StateSettings *state = &states[i];

                if((event->key_code == state->keybind) && (state != current_state)) {
                    selected_state = (selected_state == state) ? NULL : state;
                    break;
                }
            }
        }
    }
}

sapp_desc sokol_main(int argc, char* argv[]) {
    sapp_desc desc = { };
    desc.init_cb = init;
    desc.frame_cb = frame;
    desc.cleanup_cb = cleanup;
    desc.event_cb = input;
    desc.width = 1024;
    desc.height = 768;
    desc.gl_force_gles2 = true;
    desc.window_title = "MERGE";
    desc.ios_keyboard_resizes_canvas = false;
    return desc;
}