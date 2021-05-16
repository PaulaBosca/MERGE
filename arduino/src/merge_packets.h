// ---------------------------- PACKET DEFINITIONS ----------------------------
//Experiment -> Laptop
const uint8_t DataPacketID = 1; 
struct __attribute__((packed)) DataPacket {
    uint64_t timestamp;

    //Loadcell readings
    int32_t loadcell[6];

    //IMU readings
    uint32_t accel_fixed_x;
    uint32_t accel_fixed_y;
    uint32_t accel_fixed_z;

    uint32_t accel_tank1_x;
    uint32_t accel_tank1_y;
    uint32_t accel_tank1_z;
    
    uint32_t accel_tank2_x;
    uint32_t accel_tank2_y;
    uint32_t accel_tank2_z;
    
    uint32_t accel_tank3_x;
    uint32_t accel_tank3_y;
    uint32_t accel_tank3_z;

    //Flow sensor readings
    float flow_sensor[3];
};

//Experiment -> Laptop
const uint8_t PrintPacketID = 2;
//NOTE(Jon): body of a print packet is just a string

//Laptop -> Experiment
const uint8_t PumpPacketID = 3;
struct __attribute__((packed)) PumpPacket {
    //NOTE(Jon): 0 is full reverse, 0.5 is stopped, 1 is full forwards
    float pump1;
    float pump2;
};