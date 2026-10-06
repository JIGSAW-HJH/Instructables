/*
 * Teensy 3.2 Firmware - CAN Bus (MCP2515) & WS2812B NeoPixel Controller
 * 
 * Hardware Pin Mapping (from table):
 *   - MCP2515 CS   : Pin 10
 *   - MCP2515 SCK  : Pin 13
 *   - MCP2515 SI   : Pin 11
 *   - MCP2515 SO   : Pin 12
 *   - MCP2515 INT  : Pin 2
 *   - WS2812 DIN   : Pin 14 (A0)
 * 
 * WS2812 LED Sequence:
 *   LED 0: Heartbeat
 *   LED 1: TX Flash
 *   LED 2: RX Flash
 *   LED 3: Status / GUI Control
 *   LED 4: Power On Indicator
 */

#include <Arduino.h>
#include <SPI.h>
#include <mcp_can.h>
#include <Adafruit_NeoPixel.h>

// --- Corrected Pin Definitions ---
#define NEOPIXEL_PIN     14    // WS2812 Chain DIN (Pin 14 / A0)
#define NUM_LEDS         5

#define CAN0_CS          10    // MCP2515 CS
#define CAN0_INT         2     // MCP2515 INT (Pin 2)

// --- LED Index Mapping ---
#define LED_HEARTBEAT    0
#define LED_TX           1
#define LED_RX           2
#define LED_STATUS       3
#define LED_POWER        4

// --- Objects ---
Adafruit_NeoPixel strip(NUM_LEDS, NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);
MCP_CAN CAN0(CAN0_CS);

// --- Global Variables ---
String inputString = "";
bool stringComplete = false;

unsigned long lastHeartbeat = 0;
bool heartbeatState = false;

unsigned long txLedTimer = 0;
unsigned long rxLedTimer = 0;

void processCommand(String command);
void updateLeds();

void setup() {
  Serial.begin(115200);
  inputString.reserve(200);

  // Initialize WS2812B NeoPixels on Pin 14
  strip.begin();
  strip.setBrightness(50); // Brightness 0 - 255

  // Initial LED States
  strip.setPixelColor(LED_POWER, strip.Color(0, 255, 0));  // Power: Solid Green
  strip.setPixelColor(LED_STATUS, strip.Color(0, 0, 150)); // Status: Blue
  strip.setPixelColor(LED_TX, strip.Color(0, 0, 0));       // Off
  strip.setPixelColor(LED_RX, strip.Color(0, 0, 0));       // Off
  strip.show();

  // Configure MCP2515 Interrupt Pin
  pinMode(CAN0_INT, INPUT);

  // Initialize MCP2515 (CS on Pin 10, 16MHz Crystal, 500kbps)
  if (CAN0.begin(MCP_ANY, CAN_500KBPS, MCP_16MHZ) == CAN_OK) {
    CAN0.setMode(MCP_NORMAL);
    Serial.println("SYS:CAN_INIT_OK");
  } else {
    Serial.println("SYS:CAN_INIT_FAIL");
    strip.setPixelColor(LED_STATUS, strip.Color(255, 0, 0)); // Status LED Red on error
    strip.show();
  }
}

void loop() {
  // 1. Heartbeat LED Pulse (LED 0) every 500ms
  if (millis() - lastHeartbeat >= 500) {
    lastHeartbeat = millis();
    heartbeatState = !heartbeatState;
    strip.setPixelColor(LED_HEARTBEAT, heartbeatState ? strip.Color(0, 150, 0) : strip.Color(0, 0, 0));
    strip.show();
  }

  // 2. Read Incoming CAN Frame on Pin 2 Interrupt
  if (!digitalRead(CAN0_INT)) {
    long unsigned int rxId;
    unsigned char len = 0;
    unsigned char rxBuf[8];

    CAN0.readMsgBuf(&rxId, &len, rxBuf);

    // RX LED Flash (LED 2)
    strip.setPixelColor(LED_RX, strip.Color(0, 0, 255)); // Blue flash
    strip.show();
    rxLedTimer = millis();

    // Output over USB Serial
    Serial.print("CAN_RX:");
    Serial.print(rxId, HEX);
    Serial.print(":");
    for (byte i = 0; i < len; i++) {
      if (rxBuf[i] < 0x10) Serial.print("0");
      Serial.print(rxBuf[i], HEX);
    }
    Serial.println();
  }

  // 3. Read Incoming USB Serial Buffer
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n' || inChar == '\r') {
      if (inputString.length() > 0) stringComplete = true;
    } else {
      inputString += inChar;
    }
  }

  if (stringComplete) {
    inputString.trim();
    processCommand(inputString);
    inputString = "";
    stringComplete = false;
  }

  // 4. Auto Clear Temporary TX / RX LED Flashes
  updateLeds();
}

void processCommand(String command) {
  if (command == "PING") {
    Serial.println("PONG");
  }
  // CAN TX Command (e.g., CAN_TX:123:11223344)
  else if (command.startsWith("CAN_TX:")) {
    int firstColon = command.indexOf(':');
    int secondColon = command.indexOf(':', firstColon + 1);

    if (secondColon != -1) {
      String idStr = command.substring(firstColon + 1, secondColon);
      String dataStr = command.substring(secondColon + 1);

      unsigned long canId = strtoul(idStr.c_str(), NULL, 16);
      byte len = dataStr.length() / 2;
      byte txBuf[8];

      for (byte i = 0; i < len && i < 8; i++) {
        String byteStr = dataStr.substring(i * 2, (i * 2) + 2);
        txBuf[i] = (byte)strtoul(byteStr.c_str(), NULL, 16);
      }

      byte sndStat = CAN0.sendMsgBuf(canId, 0, len, txBuf);
      if (sndStat == CAN_OK) {
        Serial.println("ACK:CAN_TX:OK");
        // TX LED Flash (LED 1)
        strip.setPixelColor(LED_TX, strip.Color(255, 100, 0)); // Orange flash
        strip.show();
        txLedTimer = millis();
      } else {
        Serial.println("ERR:CAN_TX_FAIL");
      }
    }
  }
  // RGB Control for LED 3 (Status LED): SET_STATUS_LED:<R>:<G>:<B>
  else if (command.startsWith("SET_STATUS_LED:")) {
    int p1 = command.indexOf(':');
    int p2 = command.indexOf(':', p1 + 1);
    int p3 = command.indexOf(':', p2 + 1);

    if (p3 != -1) {
      byte r = command.substring(p1 + 1, p2).toInt();
      byte g = command.substring(p2 + 1, p3).toInt();
      byte b = command.substring(p3 + 1).toInt();

      strip.setPixelColor(LED_STATUS, strip.Color(r, g, b));
      strip.show();
      Serial.println("ACK:STATUS_LED_UPDATED");
    }
  }
  else {
    Serial.print("ERR:UNKNOWN_CMD:");
    Serial.println(command);
  }
}

void updateLeds() {
  // Clear TX LED after 50ms
  if (txLedTimer > 0 && (millis() - txLedTimer > 50)) {
    strip.setPixelColor(LED_TX, strip.Color(0, 0, 0));
    strip.show();
    txLedTimer = 0;
  }
  // Clear RX LED after 50ms
  if (rxLedTimer > 0 && (millis() - rxLedTimer > 50)) {
    strip.setPixelColor(LED_RX, strip.Color(0, 0, 0));
    strip.show();
    rxLedTimer = 0;
  }
}