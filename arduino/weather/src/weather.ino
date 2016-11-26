#include <SimpleDHT.h>
#include <SoftwareSerial.h>

// RX, TX
SoftwareSerial softSerial(10, 11);

const String SSID = "changeme"; // wifi_ssid
const String password = "changeme"; // wifi_password

// const String serverIp = "changeme"; // sensor_hub_ip
// const String serverPort = "changeme"; // sensor_hub_port

const unsigned long updateDelay = changeme; // update_delay

const String uuid = "changeme"; // arduino_uuid

const int DHT11_PIN = changeme; // digital_pins_dht_11
const int GREEN_LED_PIN = changeme; // digital_pins_green_led

const int NTP_PACKET_SIZE = 48;
byte packetBuffer[NTP_PACKET_SIZE];
unsigned long epochInit = 0;
unsigned long epochMesuredAt = 0;
unsigned long lastSuccessUpdate = 0;

SimpleDHT11 dht11;

struct DHT11Res {
  int temp;
  int rel_humidity;
};

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
    if (!execOnESP("AT+CIPCLOSE", "OK", 10000))
        return false;

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
        // softSerial.println("Failed to setEpoch");
        delay(10000);
    }
    return false;
}

struct DHT11Res readDHT11Retry() {
    byte temperature = 0;
    byte humidity = 0;
    int tries = 0;

    while (tries++ < 5) {
      if (!dht11.read(DHT11_PIN, &temperature, &humidity, NULL)) {
        // softSerial.println("Got from DHT11: " + temperature + " C, " + humidity + " % humidity");
        return DHT11Res {(int)temperature, (int)humidity};
      }
      delay(2000);
    }
    // softSerial.println("Tried to read 5 times from DHT11. Aborting.");
    return {99, 99};
}

boolean isResValid(struct DHT11Res res) {
  return res.temp != 99 && res.rel_humidity != 99;
}

String getBMPReqContent() {
    return "";
}

String getHygrometerReqContent() {
    return "";
}

String getDHT11ReqContent() {
    DHT11Res res = readDHT11Retry();
    if (isResValid(res)) {
      return ",dht11_4:" + String(res.temp) + ';' + String(res.rel_humidity);
    } else {
      softSerial.println("No valid DHT11 result !");
    }
    return "";
}

String buildRequestContent() {
    String content =  ((String) getEpoch());
    content += ',' + uuid;
    content += getDHT11ReqContent();
    content += getHygrometerReqContent();
    content += getBMPReqContent();
    return content;
}


void setup() {
    delay(1000);
    softSerial.begin(9600);
    Serial.begin(115200);
    pinMode(GREEN_LED_PIN, OUTPUT);

    delay(1000);
    while (!connect()) {}
    digitalWrite(GREEN_LED_PIN, 1);
}


void loop() {
    delay(1000);
    readDHT11Retry();
    softSerial.println(getDHT11ReqContent());
}
