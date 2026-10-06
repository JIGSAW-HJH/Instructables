import sys
import time
import serial
import serial.tools.list_ports
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit, QGroupBox,
    QColorDialog, QMessageBox
)
from PySide6.QtGui import QColor

# ---------------------------------------------------------------------------
# Background Serial Thread
# ---------------------------------------------------------------------------
class SerialWorker(QThread):
    data_received = Signal(str)
    connection_lost = Signal(str)

    def __init__(self, serial_port):
        super().__init__()
        self.port = serial_port
        self.running = True

    def run(self):
        while self.running and self.port and self.port.is_open:
            try:
                if self.port.in_waiting > 0:
                    line = self.port.readline().decode('utf-8', errors='replace').strip()
                    if line:
                        self.data_received.emit(line)
            except serial.SerialException as e:
                self.connection_lost.emit(str(e))
                break
            time.sleep(0.01)

    def stop(self):
        self.running = False
        self.wait()


# ---------------------------------------------------------------------------
# Main GUI Window
# ---------------------------------------------------------------------------
class TeensyCanApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Teensy 3.2 - MCP2515 CAN & WS2812B LED Controller")
        self.resize(700, 550)

        self.serial_port = None
        self.worker = None

        self.init_ui()
        self.refresh_ports()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- 1. Serial Connection Group ---
        conn_group = QGroupBox("Serial Port Settings")
        conn_layout = QHBoxLayout(conn_group)

        self.port_combobox = QComboBox()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_ports)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)

        conn_layout.addWidget(QLabel("COM Port:"))
        conn_layout.addWidget(self.port_combobox, 1)
        conn_layout.addWidget(self.refresh_btn)
        conn_layout.addWidget(self.connect_btn)
        main_layout.addWidget(conn_group)

        # --- 2. NeoPixel Status LED Control ---
        led_group = QGroupBox("NeoPixel LED 4 (Status LED) Control")
        led_layout = QHBoxLayout(led_group)

        self.color_preview = QLabel(" Status Color ")
        self.color_preview.setAlignment(Qt.AlignCenter)
        self.color_preview.setStyleSheet("background-color: blue; color: white; padding: 6px; font-weight: bold;")

        self.pick_color_btn = QPushButton("Pick Color & Set LED")
        self.pick_color_btn.setEnabled(False)
        self.pick_color_btn.clicked.connect(self.select_status_color)

        led_layout.addWidget(self.color_preview)
        led_layout.addWidget(self.pick_color_btn)
        main_layout.addWidget(led_group)

        # --- 3. CAN Bus Transmit Group ---
        can_group = QGroupBox("MCP2515 CAN Bus Transmit")
        can_layout = QHBoxLayout(can_group)

        self.can_id_input = QLineEdit()
        self.can_id_input.setPlaceholderText("ID (Hex e.g. 123)")
        self.can_id_input.setMaxLength(8)

        self.can_data_input = QLineEdit()
        self.can_data_input.setPlaceholderText("Data Bytes (Hex e.g. 11223344)")

        self.send_can_btn = QPushButton("Transmit CAN Frame")
        self.send_can_btn.setEnabled(False)
        self.send_can_btn.clicked.connect(self.send_can_frame)

        can_layout.addWidget(QLabel("CAN ID:"))
        can_layout.addWidget(self.can_id_input)
        can_layout.addWidget(QLabel("Data:"))
        can_layout.addWidget(self.can_data_input, 1)
        can_layout.addWidget(self.send_can_btn)
        main_layout.addWidget(can_group)

        # --- 4. Console Log ---
        log_group = QGroupBox("Serial / CAN Data Console")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        main_layout.addWidget(log_group)

    # --- Connection Management ---
    def refresh_ports(self):
        self.port_combobox.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combobox.addItem(f"{port.device} - {port.description}", port.device)

    def toggle_connection(self):
        if self.serial_port and self.serial_port.is_open:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        port_name = self.port_combobox.currentData()
        if not port_name:
            QMessageBox.warning(self, "Error", "Please select a serial port.")
            return

        try:
            self.serial_port = serial.Serial(port_name, 115200, timeout=1)
            self.worker = SerialWorker(self.serial_port)
            self.worker.data_received.connect(self.handle_incoming_data)
            self.worker.connection_lost.connect(self.handle_connection_loss)
            self.worker.start()

            self.connect_btn.setText("Disconnect")
            self.set_controls_enabled(True)
            self.log_message(f"Connected to {port_name}")

            self.send_command("PING")

        except Exception as e:
            QMessageBox.critical(self, "Connection Error", str(e))

    def disconnect_serial(self):
        if self.worker:
            self.worker.stop()
            self.worker = None

        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

        self.serial_port = None
        self.connect_btn.setText("Connect")
        self.set_controls_enabled(False)
        self.log_message("Disconnected.")

    def set_controls_enabled(self, enabled):
        self.pick_color_btn.setEnabled(enabled)
        self.send_can_btn.setEnabled(enabled)

    # --- Commands ---
    def send_command(self, cmd):
        if self.serial_port and self.serial_port.is_open:
            full_cmd = f"{cmd}\n"
            self.serial_port.write(full_cmd.encode('utf-8'))
            self.log_message(f"TX > {cmd}")

    def select_status_color(self):
        color = QColorDialog.getColor(QColor(0, 0, 255), self, "Select Status LED Color")
        if color.isValid():
            r, g, b = color.red(), color.green(), color.blue()
            self.color_preview.setStyleSheet(f"background-color: rgb({r},{g},{b}); color: white; padding: 6px; font-weight: bold;")
            self.send_command(f"SET_STATUS_LED:{r}:{g}:{b}")

    def send_can_frame(self):
        can_id = self.can_id_input.text().strip()
        data = self.can_data_input.text().strip()

        if not can_id or not data:
            QMessageBox.warning(self, "Input Error", "Please provide both CAN ID and Data in Hex format.")
            return

        self.send_command(f"CAN_TX:{can_id}:{data}")

    # --- Incoming Handlers ---
    @Slot(str)
    def handle_incoming_data(self, data):
        self.log_message(f"RX < {data}")

    @Slot(str)
    def handle_connection_loss(self, err):
        self.log_message(f"ERROR: Connection lost - {err}")
        self.disconnect_serial()

    def log_message(self, msg):
        self.log_text.append(msg)

    def closeEvent(self, event):
        self.disconnect_serial()
        event.accept()


# ---------------------------------------------------------------------------
# Application Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = TeensyCanApp()
    window.show()
    sys.exit(app.exec())
