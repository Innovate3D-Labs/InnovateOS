from PyQt6.QtWidgets import (QWizardPage, QVBoxLayout, QLabel, 
                            QLineEdit, QComboBox, QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt

class ConfigPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("System Configuration")
        self.setSubTitle("Configure network and printer settings for your InnovateOS installation.")
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Network configuration
        network_group = QGroupBox("Network Configuration")
        network_layout = QFormLayout()
        
        self.ssid_edit = QLineEdit()
        self.ssid_edit.setPlaceholderText("Enter WiFi network name")
        network_layout.addRow("WiFi Network:", self.ssid_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Enter WiFi password")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        network_layout.addRow("WiFi Password:", self.password_edit)
        
        network_group.setLayout(network_layout)
        self.layout.addWidget(network_group)
        
        # Printer configuration
        printer_group = QGroupBox("Printer Configuration")
        printer_layout = QFormLayout()
        
        self.printer_model = QComboBox()
        self.printer_model.addItems([
            "Prusa i3 MK3S+",
            "Creality Ender 3",
            "Other"
        ])
        printer_layout.addRow("Printer Model:", self.printer_model)
        
        self.printer_connection = QComboBox()
        self.printer_connection.addItems([
            "USB",
            "Network",
            "Serial"
        ])
        printer_layout.addRow("Connection Type:", self.printer_connection)
        
        printer_group.setLayout(printer_layout)
        self.layout.addWidget(printer_group)
        
        # Register fields
        self.registerField("wifi_ssid*", self.ssid_edit)
        self.registerField("wifi_password*", self.password_edit)
        self.registerField("printer_model*", self.printer_model, "currentText")
        self.registerField("printer_connection*", self.printer_connection, "currentText")
        
    def validatePage(self) -> bool:
        """Validate the configuration"""
        ssid = self.field("wifi_ssid")
        password = self.field("wifi_password")
        
        if len(ssid) < 1:
            self.setField("wifi_ssid", "")  # Default to empty network
            self.setField("wifi_password", "")
            
        elif len(password) < 8:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Invalid WiFi Password",
                "WiFi password must be at least 8 characters long."
            )
            return False
            
        return True
