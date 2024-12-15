from PyQt6.QtWidgets import QWizardPage, QVBoxLayout, QLabel, QCheckBox
from PyQt6.QtCore import Qt

class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to InnovateOS")
        self.setSubTitle("This wizard will help you install InnovateOS on your SD card.")
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Welcome text
        welcome_text = QLabel(
            "InnovateOS is a modern operating system for 3D printers, "
            "designed to make your printing experience as smooth as possible.\n\n"
            "This installer will:\n"
            "• Format your SD card\n"
            "• Install InnovateOS\n"
            "• Configure your network settings\n"
            "• Set up your printer\n\n"
            "Requirements:\n"
            "• An SD card with at least 1 GB of space\n"
            "• Your WiFi network name and password\n"
            "• Your printer model information"
        )
        welcome_text.setWordWrap(True)
        self.layout.addWidget(welcome_text)
        
        # Warning
        warning = QLabel(
            "\nWARNING: This will erase all data on the selected SD card!\n"
            "Please make sure you have backed up any important files."
        )
        warning.setStyleSheet("color: red; font-weight: bold;")
        warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(warning)
        
        # Agreement checkbox
        self.agreement = QCheckBox(
            "I understand that all data on the selected SD card will be erased"
        )
        self.layout.addWidget(self.agreement)
        
        # Register field
        self.registerField("agreement*", self.agreement)
