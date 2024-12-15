from PyQt6.QtWidgets import QWizardPage, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class FinishPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Installation Complete")
        self.setSubTitle("InnovateOS has been successfully installed on your SD card.")
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Success message
        success = QLabel("✅ Installation completed successfully!")
        success.setStyleSheet("color: green; font-weight: bold;")
        success.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(success)
        
        # Next steps
        next_steps = QLabel(
            "\nNext Steps:\n\n"
            "1. Remove the SD card safely from your computer\n"
            "2. Insert the SD card into your 3D printer\n"
            "3. Power on your printer\n"
            "4. Wait for the system to boot (this may take a few minutes)\n"
            "5. Connect to the WiFi network you configured\n"
            "6. Access the web interface at http://innovateos.local\n\n"
            "If you need help, please visit our documentation at:\n"
            "https://docs.innovateos.com"
        )
        next_steps.setWordWrap(True)
        self.layout.addWidget(next_steps)
        
    def initializePage(self):
        self.setFinalPage(True)
