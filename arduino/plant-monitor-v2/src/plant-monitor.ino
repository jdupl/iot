#include <SoftwareSerial.h>
#include <Wire.h>

// RX, TX
SoftwareSerial softSerial(10, 11);

const String SSID = "changeme"; // wifi_ssid
const String password = "changeme"; // wifi_password

const String iotSecret = "changeme"; // iot_secret

const String serverIp = "changeme"; // sensor_hub_ip
const String serverPort = "changeme"; // sensor_hub_port

const unsigned long updateDelay = changeme; // update_delay

const String uuid = "changeme"; // arduino_uuid
const String hygrometerPin = "changeme"; // analog_pins_hygrometer

const int RELAY_PIN = changeme; // digital_pins_relay

const int NTP_PACKET_SIZE = 48;
byte packetBuffer[NTP_PACKET_SIZE];
unsigned long epochInit = 0;
unsigned long epochMesuredAt = 0;
unsigned long lastSuccessUpdate = 0;


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

    Serial.write(packetBuffer, NTP_PACKET_SIZE);

    memset(packetBuffer, 0, NTP_PACKET_SIZE);
    bool inResPacket = false;
    char c = ' ';

    while (millis() < tExpire && i < NTP_PACKET_SIZE) {
        c = Serial.read();
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
    Serial.flush();
    softSerial.println(cmd);
    Serial.println(cmd);
    Serial.flush();

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
    execOnESP("AT+CIPCLOSE", "OK", 5000);

    unsigned long highWord = word(packetBuffer[40], packetBuffer[41]);
    unsigned long lowWord = word(packetBuffer[42], packetBuffer[43]);

    // combine the four bytes (two words) into a long integer
    epochInit = (highWord << 16 | lowWord) - 2208988800UL;
    // softSerial.println("Epoch is set");
    return true;
}

bool connectWifi() {
    return execOnESP("AT+CWMODE=1", "OK", 5000) &&
    execOnESP("AT+CWJAP=\"" + SSID + "\",\"" + password + "\"", "OK" , 15000);
}

void resetESP() {
    // Everything is broken so turn off leds
    digitalWrite(GREEN_LED_PIN, 0);

    delay(2000);
    execOnESP("AT+RST", "ready", 20000);
    delay(1000);

    if (connectWifi()) {

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
    // softSerial.println("Trying to connect to wifi");
    while (!connectWifi()) {
        // softSerial.println("Could not connect to wifi");
        delay(10000);
    }

    if (!epochNeedsUpdate()) {
        return true;
    }

    int maxTriesNTP = 3;
    int tries = 0;
    while(tries++ < maxTriesNTP) {
        if (setEpoch()) {
            return true;
        }
        delay(10000);
    }
    return false;
}

String getHygrometerReqContent() {
    String content = "";
    // Close sensors circuit
    digitalWrite(RELAY_PIN, 0);
    delay(100);
    String id = "hygro_" + (String) hygrometerPin;
    content += ',' + id + ':' + String(analogRead(hygrometerPin));
    // Open sensors circuit
    digitalWrite(RELAY_PIN, 1);

    return content;
}

String buildRequestContent() {
    return (iotSecret + "\n" + (String) getEpoch()) + ',' + uuid +  getHygrometer();
}

bool sendToSensorHub() {
    unsigned long measuredAt = getEpoch();

    String content = buildRequestContent();
    String request = "POST /api/records HTTP/1.1\r\nHost: " + serverIp + "\r\nContent-Type: text/plain\r\nContent-Length: " + content.length() + "\r\n\r\n" + content +"\r\n\r\n";

    if (!execOnESP("AT+CIPSTART=\"TCP\",\"" + serverIp + "\"," + serverPort, "OK", 5000))
    return false;

    int reqLength = request.length() + 2; // add 2 because \r\n will be appended by SoftwareSerial.println().
    if (!execOnESP("AT+CIPSEND=" + String(reqLength) , "OK", 10000)) {
        return false;
    }

    if (!execOnESP(request, "200 OK" , 15000)) {
        return false;
    }
    lastSuccessUpdate = measuredAt;
    delay(500);
    // most of the time, already closed, but make sure
    execOnESP("AT+CIPCLOSE", "OK" , 2000);

    return true;
}

void setup() {
    delay(1000);
    softSerial.begin(9600);
    Serial.begin(115200);

    pinMode(RED_LED_PIN, OUTPUT);
    pinMode(RELAY_PIN, OUTPUT);

    delay(1000);
    while (!connect()) {}
}

void loop() {
    sendToSensorHub();
    delay(updateDelay * 1000);
}
