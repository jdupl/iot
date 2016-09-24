#include <dht11.h>
#include <SoftwareSerial.h>

const int espRX = changeme; // esp_board_rx
const int espTX = changeme; // esp_board_tx
// RX, TX
SoftwareSerial softSerial(espRX, espTX);

const String SSID = "changeme"; // wifi_ssid
const String password = "changeme"; // wifi_password

const String serverIp = "changeme"; // sensor_hub_ip
const String serverPort = "changeme"; // sensor_hub_port

const unsigned long updateDelay = changeme; // update_delay
const int sensorPins[] = {changeme}; // hygrometer_pins

// Open circuit with relay when sensors are not in use to reduce oxidation
const int RELAY_PIN = changeme; // digital_pins_relay
const int DHT11_PIN = changeme; // digital_pins_dht_11
const int RED_LED_PIN = changeme; // digital_pins_red_led
const int GREEN_LED_PIN = changeme; // digital_pins_green_led

const int NTP_PACKET_SIZE = 48;
byte packetBuffer[NTP_PACKET_SIZE];
unsigned long epochInit = 0;
unsigned long epochMesuredAt = 0;
unsigned long lastSuccessUpdate = 0;

dht11 DHT11;

bool poolNTP(unsigned long timeout) {
    unsigned long tExpire = millis() + timeout;
    memset(packetBuffer, 0, NTP_PACKET_SIZE);
    int i = 0;

    packetBuffer[0] = 0b11100011;   // LI, Version, Mode
    packetBuffer[1] = 0;     // Stratum, or type of clock
    packetBuffer[2] = 6;     // Polling Interval
    packetBuffer[3] = 0xEC;  // Peer Clock Precision
    // 8 bytes of zero for Root Delay & Root Dispersion
    packetBuffer[12]  = 49;
    packetBuffer[13]  = 0x4E;
    packetBuffer[14]  = 49;
    packetBuffer[15]  = 52;

    softSerial.write(packetBuffer, NTP_PACKET_SIZE);

    memset(packetBuffer, 0, NTP_PACKET_SIZE);
    bool inResPacket = false;
    char c = ' ';

    while (millis() < tExpire && i < NTP_PACKET_SIZE) {
        c = softSerial.read();
        if (inResPacket && c != -1) {
            packetBuffer[i++] = c;
        } else if (!inResPacket && c == ':') {
            inResPacket = true;
        }
    }
    return i == NTP_PACKET_SIZE;
}

bool execOnESP(String cmd, String expectedRes, unsigned long timeout) {
    unsigned long tExpire = millis() + timeout;
    String response = "";
    // softSerial.flush();

    softSerial.println(cmd);
    Serial.println(cmd);

    while (millis() < tExpire) {
        char c = Serial.read();
        if (c >= 0) {
            response += String(c);
            if (response.indexOf(expectedRes) > 0) {
                softSerial.println(response);
                return true;
            }
        }
    }
    softSerial.println("Unexpected: " + response);
    return false;
}

bool setEpoch() {
    epochMesuredAt = millis() / 1000;

    if (!execOnESP("AT+CIPSTART=\"UDP\",\"0.ca.pool.ntp.org\",123", "OK", 5000))
        return false;
    if (!execOnESP("AT+CIPSEND=48", "OK", 5000))
        return false;
    if (!poolNTP(10000))
        return false;
    if (!execOnESP("AT+CIPCLOSE", "OK", 10000))
        return false;

    unsigned long highWord = word(packetBuffer[40], packetBuffer[41]);
    unsigned long lowWord = word(packetBuffer[42], packetBuffer[43]);

    // combine the four bytes (two words) into a long integer
    epochInit = (highWord << 16 | lowWord) - 2208988800UL;
    return true;
}

bool connectWifi() {
    return execOnESP("AT+CWMODE=1", "OK", 5000) &&
    execOnESP("AT+CWJAP=\"" + SSID + "\",\"" + password + "\"", "OK" , 15000);
}

void resetESP() {
    // Everything is broken so turn off leds
    digitalWrite(GREEN_LED_PIN, 0);
    digitalWrite(RED_LED_PIN, 0);

    delay(2000);
    execOnESP("AT+RST", "ready", 20000);
    delay(1000);

    if (connectWifi()) {
        digitalWrite(RED_LED_PIN, 1);

        if (epochInit != 0) {
            // Epoch is set
            digitalWrite(GREEN_LED_PIN, 1);
        }
    }
}

unsigned long getEpoch() {
    return epochInit + (millis() / 1000 - epochMesuredAt);
}

bool epochNeedsUpdate() {
    unsigned long expire = 86400; // every 24h
    return (epochInit + expire > getEpoch() || epochInit == 0);
}

bool connect() {
    while (!connectWifi()) {
        delay(10000);
    }
    digitalWrite(RED_LED_PIN, 1); // Wi-Fi OK (only red led on)

    if (!epochNeedsUpdate()) {
        return true;
    }

    int maxTriesNTP = 3;
    int tries = 0;
    while(tries++ < maxTriesNTP) {
        if (setEpoch()) {
            digitalWrite(RED_LED_PIN, 1); // Wi-Fi + NTP OK (both leds on)
            return true;
        }
        delay(10000);
    }
    return false;
}

void setup() {
    delay(1000);
    softSerial.begin(9600);
    delay(1000);
    softSerial.println("TEST");

    Serial.begin(115200);
    Serial.println("AT+CIOBAUD=9600");
    // execOnESP("AT+CIOBAUD=9600", "OK", 5000);
    Serial.begin(9600);
    delay(1000);
    execOnESP("AT+GMR", "OK", 5000);
    delay(1000);

    // softSerial.begin(9600);
    delay(1000);
    while (!connect()) {}

}

void loop() {

}
