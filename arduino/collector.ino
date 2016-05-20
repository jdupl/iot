// Code is based from http://rootpower.com/?p=73 and adapted for my usage
#include <SoftwareSerial.h>

SoftwareSerial softSerial(11, 10); // RX, TX
// String SSID = "wifi SSID";
// String password = "wifi password";
// String serverIp = "HTTP server ip";

void setup() {
    softSerial.begin(115200);
    delay(1000);
    softSerial.println("AT+CIOBAUD=9600");
    delay(1000);
    softSerial.begin(9600);
    Serial.begin(9600);
    delay(1000);
    reset();
}

void loop() {
    bool err = false;
    if (!execOnESP("AT+CIPSTART=\"TCP\",\"" + serverIp + "\",80", "OK", 5000)) {
        err = true;
    } else {
        String request = "GET / HTTP/1.1\r\n";
        int reqLength = request.length() + 2; // add 2 because \r\n will be appended by SoftwareSerial.println().

        if (!execOnESP("AT+CIPSEND=" + String(reqLength) , "OK" , 10000)) {
            err = true;
        }
    }
    delay(3000);
}

void reset() {
    execOnESP("AT+RST", "ready", 20000);
    execOnESP("AT+CWMODE=1", "OK", 5000);
    execOnESP("AT+CWJAP=\"" + SSID + "\",\"" + password + "\"", "OK" , 15000);
}

bool execOnESP(String cmd, String expectedRes, unsigned long timeout) {
    unsigned long tnow = millis();
    unsigned long tstart = millis();
    String response = "";

    while (tnow > tstart + timeout) {
        char c = softSerial.read();
        if (c >= 0) {
            response += String(c);
            if (response == expectedRes) {
                return true;
            }
        }
    }
    return false
}
