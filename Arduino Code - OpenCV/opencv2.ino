#include <ESP8266WiFi.h>
#include <Servo.h>

// WiFi Credentials
const char* ssid = "rAchELs iPhOnE???";  // Replace with your WiFi Name
const char* password = "rachelrachel";   // Replace with your WiFi Password

WiFiServer server(80);  // Start Web Server on Port 80

Servo thumbServo, indexServo, middleServo, ringServo, pinkyServo;

int thumbPos = 0, indexPos = 0, middlePos = 0, ringPos = 180, pinkyPos = 0;

void setup() {
    Serial.begin(115200);
    delay(1000); // Small delay to stabilize Serial Monitor output

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nAlready connected to WiFi!");
    } else {
        Serial.print("Connecting to WiFi...");
        WiFi.begin(ssid, password);
        while (WiFi.status() != WL_CONNECTED) {
            delay(500);
            Serial.print(".");
        }
        Serial.println("\nWiFi connected!");
    }

    // Print IP address regardless of when it connects
    Serial.print("ESP8266 IP: ");
    Serial.println(WiFi.localIP());

    // Start Server
    server.begin();

    // Attach Servos to GPIO Pins
    thumbServo.attach(D1);
    indexServo.attach(D2);
    middleServo.attach(D3);
    ringServo.attach(D4);
    pinkyServo.attach(D5);

    // Move servos to initial positions
    updateAllServos();
}

void loop() {
    WiFiClient client = server.available();
    if (!client) return;

    while (!client.available()) {
        delay(1);
    }

    String request = client.readStringUntil('\r');
    client.flush();

    // Check which fingers are open/closed and update positions
    if (request.indexOf("F8=Open") != -1) indexPos = 180;
    if (request.indexOf("F8=Closed") != -1) indexPos = 0;

    if (request.indexOf("F20=Open") != -1) pinkyPos = 0;
    if (request.indexOf("F20=Closed") != -1) pinkyPos = 180;

    if (request.indexOf("F16=Open") != -1) ringPos = 0;
    if (request.indexOf("F16=Closed") != -1) ringPos = 180;

    if (request.indexOf("F12=Open") != -1) middlePos = 0;
    if (request.indexOf("F12=Closed") != -1) middlePos = 180;

    if (request.indexOf("F4=Open") != -1) thumbPos = 180;
    if (request.indexOf("F4=Closed") != -1) thumbPos = 0;

    // Move all servos simultaneously
    updateAllServos();

    // Send HTTP Response
    client.println("HTTP/1.1 200 OK");
    client.println("Content-Type: text/html");
    client.println();
    client.println("OK");
    client.stop(); // Close the connection
}

// Function to move all servos at once
void updateAllServos() {
    thumbServo.write(thumbPos);
    indexServo.write(indexPos);
    middleServo.write(middlePos);
    ringServo.write(ringPos);
    pinkyServo.write(pinkyPos);

    Serial.println("Updated Servo Positions:");
    Serial.print("Thumb: "); Serial.print(thumbPos);
    Serial.print(" | Index: "); Serial.print(indexPos);
    Serial.print(" | Middle: "); Serial.print(middlePos);
    Serial.print(" | Ring: "); Serial.print(ringPos);
    Serial.print(" | Pinky: "); Serial.println(pinkyPos);
}
