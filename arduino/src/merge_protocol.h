#include <stdint.h>

//Packet Format:
//0:              uint8_t StartByte = 0xFE
//1:              uint16_t PayloadLen
//3:              uint8_t PacketType
//4:              Payload ...
//4 + PayloadLen: uint16_t Checksum (checksum of all bytes aside from the checksum)

//Byte substitution:
//0xFE -> 0xEE 0x00
//0xEE -> 0xEE 0x01

// ---------------------------- PACKET RECEIVING ----------------------------

//Decodes 'b_in', returning true & writing the result to 'b_out' if a non-escape byte was recieved
bool decodeByte(uint8_t *b_out, uint8_t b_in) {
    static bool RecvByteEscaped = false;
    if(RecvByteEscaped) {
        RecvByteEscaped = false;
        switch(b_in) {
            case 0x00: *b_out = 0xFE; return true;
            case 0x01: *b_out = 0xEE; return true;
            default: return false; //Error
        }
    } else {
        if(b_in == 0xEE) {
            RecvByteEscaped = true;
            return false;
        } else {
            *b_out = b_in;
            return true;
        }
    }
}

struct MERGEPacket {
    uint8_t type;
    uint16_t len;
    uint8_t *payload;
};

bool recvPacket(MERGEPacket *packet, uint8_t in_b) {
    const uint16_t MAX_PAYLOAD_LEN = 1024;
    static uint32_t recv_loc = 0; //Current byte in the current packet
    static uint16_t current_packet_checksum = 0; //Current checksum of the current packet  
    
    //Fields of packet currently being recieved
    static uint16_t PayloadLen = 0; 
    static uint8_t PacketType = 0;
    static uint8_t Payload[MAX_PAYLOAD_LEN] = {};
    static uint16_t Checksum = 0;
    
    //Reset state machine if we see the start byte, thats the only way
    //it should be able to show up *before* byte substitution
    if(in_b == 0xFE) recv_loc = 0;

    //decodeByte takes care of byte substitution
    uint8_t b;
    if(decodeByte(&b, in_b)) {
    
        //Byte recieved, advance packet revieving state machine
        if(recv_loc == 0) { //StartByte
            current_packet_checksum = b; //Reset running checksum to current byte
            if(in_b == 0xFE) recv_loc++; //Advance when we see the raw start byte 0xFE
        } else if(recv_loc == 1) { //PayloadLen LSB
            PayloadLen = (uint16_t)b;

            current_packet_checksum += b;
            recv_loc++;
        } else if(recv_loc == 2) { //PayloadLen MSB
            PayloadLen = PayloadLen | ((uint16_t)b << 8);
            
            current_packet_checksum += b;
            recv_loc++;

            //Skip packet if its larger than max size
            if(PayloadLen > MAX_PAYLOAD_LEN) recv_loc = 0;
        } else if(recv_loc == 3) { //PacketType
            PacketType = b;

            current_packet_checksum += b;
            recv_loc++;
        } else if((4 <= recv_loc) && (recv_loc < (4 + PayloadLen) )) { //Payload
            Payload[recv_loc - 4] = b;

            current_packet_checksum += b;
            recv_loc++;
        } else if(recv_loc == (4 + PayloadLen)) { //Checksum LSB
            Checksum = (uint16_t)b;
            recv_loc++;
        } else if(recv_loc == (5 + PayloadLen)) { //Checksum MSB
            Checksum = Checksum | ((uint16_t)b << 8);
            recv_loc = 0;
            
            if(Checksum == current_packet_checksum) {
                //Packet checksum matches the one we computed, packet is correct
                packet->type = PacketType;
                packet->len = PayloadLen;
                packet->payload = Payload;
                return true;
            }
        }
    }

    return false;
}

// ---------------------------- PACKET SENDING ----------------------------

//Encodes the byte 'b' and writes it to serial,
//also adds the unencoded 'b' to 'checksum' if its not NULL  
void writeByte(uint8_t b, uint16_t *checksum) {
    if(checksum != NULL) (*checksum) += b;

    if(b == 0xFE) {
        //0xFE -> 0xEE 0x00
        Serial.write(0xEE);
        Serial.write(0x00);
    } else if(b == 0xEE) {
        //0xEE -> 0xEE 0x01
        Serial.write(0xEE);
        Serial.write(0x01);
    } else {
        Serial.write(b);
    }
}

void sendPacket(uint8_t *payload, uint16_t len, uint8_t type) {
    //Start checksum with raw start byte & write the start byte
    uint16_t checksum = 0xFE;
    Serial.write(0xFE);

    writeByte((uint8_t)((len >> 0) & 0xFF), &checksum); //PayloadLen LSB
    writeByte((uint8_t)((len >> 8) & 0xFF), &checksum); //PayloadLen MSB
    writeByte(type, &checksum); //PacketType

    //Payload    
    for(uint16_t j = 0; j < len; j++) writeByte(payload[j], &checksum);

    writeByte((uint8_t)((checksum >> 0) & 0xFF), NULL); //Checksum LSB
    writeByte((uint8_t)((checksum >> 8) & 0xFF), NULL); //Checksum MSB
}
