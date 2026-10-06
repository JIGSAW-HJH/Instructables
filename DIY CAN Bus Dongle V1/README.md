# Open CAN-Bus USB Dongle & PySide6 Diagnostic Suite

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licensestps://img.shields.io/badge/Python-3.10%2B-blue://www.python.org/)
[![Qt](https://img.shields.io/badge/Qt-PySide6-green.svg)](https://pproject/PySide6/)
[![Hardware](https://img.shields.io/badge/Hardware-Teensy%203.2%20%7C%20MCP2515-orange.svg)](#hardware-configuration)

<img width="1536" height="1024" alt="Designer" src="https://github.com/user-attachments/assets/d22e46ad-f39d-43ee-a412-1c5f28295ef0" />

An open-source USB-to-CAN bus adapter and desktop diagnostic application built around a Teensy 3.2 microcontroller and MCP2515 CAN controller.

The project combines custom Arduino firmware, CAN bus monitoring and transmission capabilities, WS2812 RGB status indicators, and a Python/PySide6 desktop interface for real-time CAN network diagnostics and testing.

Originally developed as part of the BACAR (Balloon Carrying Amateur Radio) ground station project to provide a low-cost and easily reproducible CAN bus interface for telemetry and control systems.

---

## Key Features

* USB-to-CAN bus bridge using a Teensy 3.2 and MCP2515 controller.
* Real-time CAN frame monitoring and display.
* Manual CAN frame transmission from the desktop application.
* Interrupt-driven CAN reception for responsive bus monitoring.
* WS2812 RGB status indication system with heartbeat, TX, RX, power, and user-controlled status LEDs.
* Simple ASCII-based serial control protocol.
* PySide6 desktop GUI with asynchronous serial communications.
* Cross-platform support for Windows, Linux, and macOS.
* Open-source hardware, firmware, and software ecosystem.

---


A low-cost, open-source USB-to-CAN interface built from commonly available components. This project combines a Teensy 3.2 microcontroller, MCP2515 CAN controller, custom firmware, and a Python PySide6 desktop application to create a capable CAN bus development and diagnostics tool.





## Overview

Commercial USB-to-CAN adapters can be expensive, especially for hobbyists, educators, and experimental projects. This project was developed as part of a ground station system for the BACAR (Balloon Carrying Amateur Radio) project, where a reliable CAN interface was needed to communicate with antenna rotators and telemetry systems.

Rather than purchasing proprietary hardware, this adapter was built entirely from parts-bin components while maintaining reliability, expandability, and ease of use.

## Features

- USB-to-CAN communication bridge
- Teensy 3.2 based hardware platform
- MCP2515 CAN controller
- Standard DB9 CAN connector
- Optional onboard 120Ω bus termination
- 5x WS2812 RGB status LEDs
- PySide6 desktop GUI
- Real-time CAN monitoring
- CAN frame transmission
- Open-source firmware and software
- Windows and Linux compatible

## System Architecture

```text
Laptop (PySide6 GUI)
        │
   USB Serial
        │
DIY USB-CAN Dongle
        │
      CAN Bus
        │
┌─────────────┬─────────────┐
│             │             │
Rotator    Telemetry    Sensors
Controller   Nodes      Devices
```

## Hardware Components

### Required Electronics

- Teensy 3.2
- MCP2515 CAN controller module
- MCP2551/TJA1050 CAN transceiver (depending on module version)
- DB9 panel-mount connector
- 5 × WS2812 RGB LEDs
- 330Ω to 470Ω resistor for NeoPixel data line
- Hookup wire
- USB cable
- Optional 120Ω CAN termination resistor

### Tools

- Soldering iron
- Solder and flux
- Wire cutters
- Wire strippers
- Small screwdrivers
- Hot glue or super glue
- 3D printer (optional)

## Status LED Functions

| LED | Function | Color |
|------|----------|--------|
| 0 | Heartbeat | Green pulse |
| 1 | CAN Transmit | Orange flash |
| 2 | CAN Receive | Blue flash |
| 3 | User Status | User selectable |
| 4 | Power | Solid green |

## CAN Connection

Standard DB9 CAN wiring is used.

| Pin | Function |
|------|-----------|
| 2 | CAN Low (CAN_L) |
| 7 | CAN High (CAN_H) |
| Others | As required by CiA standard |

If the adapter is located at the end of the CAN network, ensure the 120Ω termination resistor is enabled.

## Firmware Features

The Teensy firmware acts as a bridge between USB Serial and the CAN bus.

### Functions

- CAN frame reception
- CAN frame transmission
- USB serial command processing
- RGB LED status indication
- Interrupt-driven CAN reception
- Non-blocking task scheduling

## Serial Command Protocol

The Teensy firmware communicates using a simple ASCII text-based protocol over USB Serial at **115200 baud**.

Each command must be terminated with a newline (`\n`) or carriage return (`\r`).

---

### PING

Used to verify communication between the host application and the Teensy.

#### Command

```text
PING
```

#### Response

```text
PONG
```

#### Example

```text
TX > PING
RX < PONG
```

---

### CAN_TX

Transmit a CAN frame onto the bus.

#### Command Format

```text
CAN_TX:<CAN_ID>:<DATA>
```

#### Parameters

| Parameter | Description |
|------------|------------|
| `<CAN_ID>` | CAN Identifier in hexadecimal |
| `<DATA>` | Payload bytes as a continuous hexadecimal string |

#### Example

```text
CAN_TX:123:11223344
```

This transmits:

| Field | Value |
|---------|---------|
| CAN ID | 0x123 |
| DLC | 4 |
| Data | 11 22 33 44 |

#### Success Response

```text
ACK:CAN_TX:OK
```

#### Error Response

```text
ERR:CAN_TX_FAIL
```

#### Example Transaction

```text
TX > CAN_TX:123:11223344
RX < ACK:CAN_TX:OK
```

---

### SET_STATUS_LED

Controls the RGB color of the Status LED (LED 3).

#### Command Format

```text
SET_STATUS_LED:<R>:<G>:<B>
```

#### Parameters

| Parameter | Range |
|------------|------------|
| R | 0 - 255 |
| G | 0 - 255 |
| B | 0 - 255 |

#### Example

```text
SET_STATUS_LED:0:0:255
```

Sets the Status LED to blue.

#### Response

```text
ACK:STATUS_LED_UPDATED
```

#### Example Transaction

```text
TX > SET_STATUS_LED:255:0:0
RX < ACK:STATUS_LED_UPDATED
```

---

## Automatic Messages Generated by Firmware

The firmware can also send messages to the host without being requested.

### CAN_RX

Generated whenever a CAN frame is received from the MCP2515.

#### Format

```text
CAN_RX:<CAN_ID>:<DATA>
```

#### Example

```text
CAN_RX:120:01020304
```

Decoded as:

| Field | Value |
|---------|---------|
| CAN ID | 0x120 |
| Data | 01 02 03 04 |

These messages are automatically displayed in the PySide6 console.

---

### System Startup Messages

When the Teensy powers up, CAN initialization status is reported.

#### Successful Initialization

```text
SYS:CAN_INIT_OK
```

#### Failed Initialization

```text
SYS:CAN_INIT_FAIL
```

If initialization fails, the Status LED turns red.

---

### Unknown Command Error

If an invalid command is received, the firmware returns:

```text
ERR:UNKNOWN_CMD:<COMMAND>
```

#### Example

```text
TX > TEST
RX < ERR:UNKNOWN_CMD:TEST
```

---

## Complete Protocol Summary

| Direction | Message |
|------------|------------|
| PC → Teensy | `PING` |
| Teensy → PC | `PONG` |
| PC → Teensy | `CAN_TX:<ID>:<DATA>` |
| Teensy → PC | `ACK:CAN_TX:OK` |
| Teensy → PC | `ERR:CAN_TX_FAIL` |
| PC → Teensy | `SET_STATUS_LED:<R>:<G>:<B>` |
| Teensy → PC | `ACK:STATUS_LED_UPDATED` |
| Teensy → PC | `CAN_RX:<ID>:<DATA>` |
| Teensy → PC | `SYS:CAN_INIT_OK` |
| Teensy → PC | `SYS:CAN_INIT_FAIL` |
| Teensy → PC | `ERR:UNKNOWN_CMD:<COMMAND>` |

## Desktop Application

The desktop control program is written in Python using the PySide6 (Qt6) framework and communicates with the Teensy over USB Serial.

A dedicated background thread continuously monitors incoming serial data, ensuring the user interface remains responsive while CAN messages are being received.

<img width="699" height="578" alt="Screenshot 2026-10-06 084902" src="https://github.com/user-attachments/assets/1def19a4-a204-4a23-a1a4-b3095937ca62" />


### Main Functions

#### Serial Port Management

The application automatically scans for available serial devices and allows the user to:

- Refresh available COM ports
- Connect to a Teensy device
- Disconnect from an active session
- Monitor connection status

When a connection is established the software automatically sends a:

```text
PING
```

command to verify communication with the firmware.

---

#### Status LED Control

The GUI provides a color picker used to control the Teensy's Status LED (LED 3).

Users can:

- Select any RGB color
- Preview the selected color
- Send the selected color directly to the Teensy

Example command:

```text
SET_STATUS_LED:0:0:255
```

---

#### CAN Bus Transmission

The CAN transmission panel allows users to manually transmit CAN messages onto the network.

Inputs:

- CAN Identifier (Hex)
- CAN Data Payload (Hex)

Example:

```text
CAN_TX:123:11223344
```

---

#### Real-Time CAN Monitoring

The software continuously listens for incoming serial traffic from the Teensy and displays:

- Received CAN messages
- CAN transmit acknowledgements
- System status messages
- Error messages

Example displayed messages:

```text
RX < CAN_RX:120:01020304
RX < ACK:CAN_TX:OK
RX < SYS:CAN_INIT_OK
RX < ERR:CAN_TX_FAIL
```

---

#### Background Thread Architecture

Serial communication is handled by the `SerialWorker` class, which runs in its own `QThread`.

This architecture prevents:

- GUI freezing
- Serial read blocking
- Missed CAN messages
- Unresponsive controls

The GUI thread is responsible only for:

- Window updates
- User interactions
- Logging
- Command generation

The background thread is responsible for:

- Reading serial data
- Detecting connection loss
- Forwarding received messages to the GUI

### Software Dependencies

Install required packages:

```bash
pip install PySide6 pyserial
```

### Launching the Application

```bash
python main.py
```

### Building a Standalone Windows Executable

Install PyInstaller:

```bash
pip install pyinstaller
```

Build:

```bash
pyinstaller --noconfirm --onedir --windowed --name "TeensyController" main.py
```

Output location:

```text
dist/TeensyController/
```

## Arduino IDE Setup

### Install Teensy Support

Add the following Boards Manager URL:

```text
https://www.pjrc.com/teensy/package_teensy_index.json
```

Then install:

- Teensy Board Package

### Required Libraries

Install the following libraries through Library Manager:

- MCP_CAN_lib by coryjfowler
- Adafruit NeoPixel

## Hardware Configuration

### Teensy Connections

| Signal | Teensy Pin |
|----------|-----------|
| NeoPixel Data | Pin 14 |
| MCP2515 CS | Pin 10 |
| MCP2515 INT | Pin 2 |
| SPI SCK | Pin 13 |
| SPI MOSI | Pin 11 |
| SPI MISO | Pin 12 |

### CAN Settings

Default configuration:

- CAN Speed: 500 kbps
- MCP2515 Crystal: 16 MHz

Adjust firmware settings if your module uses an 8 MHz crystal.

## Troubleshooting

### CAN Network Not Working

Check:

- CAN_H and CAN_L wiring
- Bus termination resistors
- CAN baud rate
- MCP2515 crystal frequency

### Serial Port Busy

Ensure no other software is using the COM port:

- Arduino Serial Monitor
- PuTTY
- TeraTerm
- Other serial software

### Linux Permissions

Add your user to the dialout group:

```bash
sudo usermod -aG dialout $USER
```

Log out and back in afterward.

## Project Files

```text
CanController
