#include <Arduino.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <stdarg.h>
#include "merge_protocol.h"
#include "merge_packets.h"

//Motor-Controllers----------------------------------------
const int pump_0_pin = 6;
const int pump_1_pin = 5;

//Flow-Sensor----------------------------------------------
#define FLOW_SENSOR_COUNT 3
const int flow_sensor_pins[FLOW_SENSOR_COUNT] = {2, 18, 19};
volatile uint32_t flow_sensor_counts[FLOW_SENSOR_COUNT] = {};
void flowSensor0Interrupt() { flow_sensor_counts[0]++; }
void flowSensor1Interrupt() { flow_sensor_counts[1]++; }
void flowSensor2Interrupt() { flow_sensor_counts[2]++; }

uint64_t last_time;
uint64_t last_flow_time;
uint64_t last_pump_set_time;
uint64_t last_pump_step_time;
uint64_t stop_sync_led_time;

//Load-Cell----------------------------------------------
#include <HX711.h>

#define LOADCELL_COUNT 6
const int LOADCELL_DOUT_PINS[LOADCELL_COUNT] = {24, 26, 29, 30, 32, 34};
const int LOADCELL_SCK_PINS[LOADCELL_COUNT] = {25, 27, 28, 31, 33, 35};

HX711 loadcells[LOADCELL_COUNT];

//IMU--------------------------------------------------
#define APIN_FIXED_X 0
#define APIN_FIXED_Y 1
#define APIN_FIXED_Z 2

#define APIN_TANK1_X 3
#define APIN_TANK1_Y 4
#define APIN_TANK1_Z 5

#define APIN_TANK2_X 6
#define APIN_TANK2_Y 7
#define APIN_TANK2_Z 8

#define APIN_TANK3_X 9
#define APIN_TANK3_Y 10
#define APIN_TANK3_Z 11

void sendPrintPacket(const char *format, ...) {
    char pbuffer[256];
    va_list args;
    va_start(args, format);
    vsnprintf(pbuffer, 256, format, args);
    va_end(args);

    sendPacket((uint8_t *)pbuffer, strlen(pbuffer), PrintPacketID);
}

const int sync_led_pin = 9;

void setup() {
    Serial.begin(115200);
    while(!Serial){}

    //Motor controller pins init
    pinMode(pump_0_pin, OUTPUT);
    pinMode(pump_1_pin, OUTPUT);

    //Flow sensor init
    pinMode(flow_sensor_pins[0], INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(flow_sensor_pins[0]), &flowSensor0Interrupt, RISING);

    pinMode(flow_sensor_pins[1], INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(flow_sensor_pins[1]), &flowSensor1Interrupt, RISING);

    pinMode(flow_sensor_pins[2], INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(flow_sensor_pins[2]), &flowSensor2Interrupt, RISING);  

    //Load cell init
    for(int i = 0; i < LOADCELL_COUNT; i++) {
        loadcells[i].begin(LOADCELL_DOUT_PINS[i], LOADCELL_SCK_PINS[i]);
    }

    pinMode(sync_led_pin, OUTPUT);

    last_time = millis();
    last_flow_time = last_time;
    last_pump_set_time = last_time;
    last_pump_step_time = last_time;
    stop_sync_led_time = last_time;
}

int clamp(int _min, int _max, int val) {
    if(val > _max)
        return _max;

    if(val < _min)
        return _min;
        
    return val;
}

int sign(int x) {
    return (x < 0) ? -1 : 1;
}

int abs_(int x) {
    return (x < 0) ? -x : x;
}

const int pwm_min = 128;
const int pwm_max = 250;
const int pwm_stopped = (pwm_max + pwm_min) / 2;

const uint64_t pwm_step_time = 100; // 100 ms
const int pwm_max_step = 5;

int pump0_output = pwm_stopped;
int pump1_output = pwm_stopped;

int pump0_setpoint = pwm_stopped;
int pump1_setpoint = pwm_stopped;

int32_t loadcell_readings[LOADCELL_COUNT] = {};
float flow_sensor_readings[FLOW_SENSOR_COUNT] = {};

void loop() {
    //Recieve incoming bytes from serial and feed to state machine
    while(Serial.available() > 0) {
        uint8_t data = Serial.read();
        
        MERGEPacket packet;
        if(recvPacket(&packet, data)) {

            //we have a recieved packet, handle it
            if((packet.type == PumpPacketID) && (packet.len == sizeof(PumpPacket))) {
                PumpPacket *pump_packet = (PumpPacket *)packet.payload;
                int new_pump0_setpoint = pwm_min + (int)((pwm_max - pwm_min) * pump_packet->pump1);
                int new_pump1_setpoint = pwm_min + (int)((pwm_max - pwm_min) * pump_packet->pump2);

                if((new_pump0_setpoint != pump0_setpoint) || (new_pump1_setpoint != pump1_setpoint)) {
                    pump0_setpoint = new_pump0_setpoint;
                    pump1_setpoint = new_pump1_setpoint;

                    digitalWrite(sync_led_pin, HIGH);
                    stop_sync_led_time = millis() + 1000 /*1 sec*/;
                }

                last_pump_set_time = millis();
            }
        }
    }

    if(millis() >= stop_sync_led_time) {
        digitalWrite(sync_led_pin, LOW);
    }
    
    //pump watchdog timer (stop pumps if we lose comms)
    if((millis() - last_pump_set_time) >= 4000/*4 sec*/) {
        pump0_setpoint = pwm_stopped;
        pump1_setpoint = pwm_stopped;

        pump0_output = pump0_setpoint;
        pump1_output = pump1_setpoint;
    }

    //pump output ramping
    if((millis() - last_pump_step_time) >= pwm_step_time) {
        int pump0_step_sign = sign(pump0_setpoint - pump0_output);
        int pump0_step_size = clamp(0, pwm_max_step, abs_(pump0_setpoint - pump0_output));
        pump0_output += pump0_step_sign*pump0_step_size;

        int pump1_step_sign = sign(pump1_setpoint - pump1_output);
        int pump1_step_size = clamp(0, pwm_max_step, abs_(pump1_setpoint - pump1_output));
        pump1_output += pump1_step_sign*pump1_step_size;

        last_pump_step_time = millis();
    }

    //PWM output
    analogWrite(pump_0_pin, clamp(pwm_min, pwm_max, pump0_output));
    analogWrite(pump_1_pin, clamp(pwm_min, pwm_max, pump1_output));

    //Read values from loadcells when they become available
    for(int i = 0; i < LOADCELL_COUNT; i++) {
        if (loadcells[i].is_ready()) {
            loadcell_readings[i] = loadcells[i].read();        
        }
    }

    uint64_t curr_time = millis();
    uint64_t dt_millis = curr_time - last_time;
    uint64_t dt_flow_millis = curr_time - last_flow_time;

    //Calculate new flow values every second & clear the flow sensor counts
    if(dt_flow_millis >= 1000/*1 sec*/) {
        float dt_flow = (float)dt_flow_millis / 1000.0;
        last_flow_time = curr_time;

        for(int i = 0; i < FLOW_SENSOR_COUNT; i++) {
            //NOTE(Jon): 21 is from the back of the flow sensor
            flow_sensor_readings[i] = flow_sensor_counts[i] / (dt_flow * 21);
            flow_sensor_counts[i] = 0;
        }
    }

    //Send data packet every 10ms
    if(dt_millis >= 10/*ms*/) {
        last_time = curr_time;

        DataPacket data_packet = {};
        data_packet.timestamp = curr_time;

        //copy loadcell readings
        for(int i = 0; i < LOADCELL_COUNT; i++) {
            data_packet.loadcell[i] = loadcell_readings[i];
        }

        //imu readings
        data_packet.accel_fixed_x = analogRead(APIN_FIXED_X);
        data_packet.accel_fixed_y = analogRead(APIN_FIXED_Y);
        data_packet.accel_fixed_z = analogRead(APIN_FIXED_Z);
    
        data_packet.accel_tank1_x = analogRead(APIN_TANK1_X);
        data_packet.accel_tank1_y = analogRead(APIN_TANK1_Y);
        data_packet.accel_tank1_z = analogRead(APIN_TANK1_Z);
        
        data_packet.accel_tank2_x = analogRead(APIN_TANK2_X);
        data_packet.accel_tank2_y = analogRead(APIN_TANK2_Y);
        data_packet.accel_tank2_z = analogRead(APIN_TANK2_Z);
        
        data_packet.accel_tank3_x = analogRead(APIN_TANK3_X);
        data_packet.accel_tank3_y = analogRead(APIN_TANK3_Y);
        data_packet.accel_tank3_z = analogRead(APIN_TANK3_Z);
    
        //copy flow sensor readings
        for(int i = 0; i < FLOW_SENSOR_COUNT; i++) {
            data_packet.flow_sensor[i] = flow_sensor_readings[i];
        }

        sendPacket((uint8_t *)&data_packet, sizeof(data_packet), DataPacketID);
    }
}
