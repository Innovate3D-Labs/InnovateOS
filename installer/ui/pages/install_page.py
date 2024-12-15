from PyQt6.QtWidgets import QWizardPage, QVBoxLayout, QProgressBar, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from utils.installer import InstallerManager

class InstallationWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, installer: InstallerManager, drive: str, config: dict):
        super().__init__()
        self.installer = installer
        self.drive = drive
        self.config = config
        
    def run(self):
        try:
            # Download system image (20%)
            self.progress.emit(0, "Downloading system image...")
            image_path = self.installer.download_system_image()
            if not image_path:
                self.finished.emit(False, "Failed to download system image")
                return
            self.progress.emit(20, "System image downloaded")
            
            # Verify checksum (30%)
            self.progress.emit(20, "Verifying system image...")
            if not self.installer.verify_image_checksum(image_path):
                self.finished.emit(False, "System image verification failed")
                return
            self.progress.emit(30, "System image verified")
            
            # Prepare drive (50%)
            self.progress.emit(30, "Preparing drive...")
            if not self.installer.prepare_drive(self.drive):
                self.finished.emit(False, "Drive preparation failed")
                return
            self.progress.emit(50, "Drive prepared")
            
            # Write image (70%)
            self.progress.emit(50, "Writing system image...")
            if not self.installer.write_image_to_drive(image_path, self.drive):
                self.finished.emit(False, "Failed to write system image")
                return
            self.progress.emit(70, "System image written")
            
            # Configure system (90%)
            self.progress.emit(70, "Configuring system...")
            if not self.installer.configure_system(self.drive, self.config):
                self.finished.emit(False, "System configuration failed")
                return
            self.progress.emit(90, "System configured")
            
            # Verify installation (100%)
            self.progress.emit(90, "Verifying installation...")
            if not self.installer.verify_installation(self.drive):
                self.finished.emit(False, "Installation verification failed")
                return
            self.progress.emit(100, "Installation complete")
            
            self.installer.cleanup()
            self.finished.emit(True, "Installation completed successfully")
            
        except Exception as e:
            self.finished.emit(False, f"Installation failed: {str(e)}")

class InstallPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Installing InnovateOS")
        self.setSubTitle("Please wait while InnovateOS is being installed...")
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_label)
        
        self.installer = InstallerManager()
        self.worker = None
        
    def initializePage(self):
        drive = self.field("selected_drive")
        config = {
            "system": {},
            "network": {
                "ssid": self.field("wifi_ssid"),
                "password": self.field("wifi_password")
            },
            "printer": {
                "model": self.field("printer_model"),
                "connection": self.field("printer_connection")
            }
        }
        
        self.worker = InstallationWorker(self.installer, drive, config)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.installation_finished)
        self.worker.start()
        
    def update_progress(self, value: int, message: str):
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        
    def installation_finished(self, success: bool, message: str):
        if success:
            self.wizard().next()
        else:
            self.status_label.setText(f"Error: {message}")
            self.wizard().back()
            
    def isComplete(self) -> bool:
        return False  # Disable Next button during installation
