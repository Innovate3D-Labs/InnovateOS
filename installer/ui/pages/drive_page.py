from PyQt6.QtWidgets import (QWizardPage, QVBoxLayout, QLabel, 
                            QPushButton, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt
import humanize
from utils.installer import InstallerManager

class DrivePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Select Installation Drive")
        self.setSubTitle("Please select the SD card where InnovateOS will be installed.")
        
        self.installer = InstallerManager()
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Warning label
        warning = QLabel(
            "WARNING: All data on the selected drive will be erased!\n"
            "Please make sure you have selected the correct drive."
        )
        warning.setStyleSheet("color: red; font-weight: bold;")
        warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(warning)
        
        # Drive selection
        self.drive_combo = QComboBox()
        self.layout.addWidget(self.drive_combo)
        
        # Drive info
        self.drive_info = QLabel()
        self.drive_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.drive_info)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Drive List")
        refresh_btn.clicked.connect(self.refresh_drives)
        self.layout.addWidget(refresh_btn)
        
        # Register fields
        self.registerField("selected_drive*", self.drive_combo, "currentText")
        
    def initializePage(self):
        self.refresh_drives()
        
    def refresh_drives(self):
        """Refresh the list of available drives"""
        self.drive_combo.clear()
        drives = self.installer.get_available_drives()
        
        if not drives:
            QMessageBox.warning(
                self,
                "No Drives Found",
                "No removable drives were found.\n"
                "Please insert an SD card and click Refresh."
            )
            return
        
        for drive in drives:
            size = humanize.naturalsize(drive['size'])
            free = humanize.naturalsize(drive['free_space'])
            label = f"{drive['letter']} - {drive['label']} ({size})"
            self.drive_combo.addItem(label, drive)
            
        self.drive_combo.currentIndexChanged.connect(self.update_drive_info)
        self.update_drive_info()
        
    def update_drive_info(self):
        """Update the drive information display"""
        if self.drive_combo.currentData():
            drive = self.drive_combo.currentData()
            size = humanize.naturalsize(drive['size'])
            free = humanize.naturalsize(drive['free_space'])
            self.drive_info.setText(
                f"Size: {size}\n"
                f"Free Space: {free}\n"
                f"Drive Letter: {drive['letter']}"
            )
        else:
            self.drive_info.clear()
            
    def validatePage(self) -> bool:
        """Validate the selected drive"""
        if not self.drive_combo.currentData():
            QMessageBox.warning(
                self,
                "No Drive Selected",
                "Please select a drive to continue."
            )
            return False
            
        drive = self.drive_combo.currentData()
        required_space = 1024 * 1024 * 1024  # 1 GB
        
        if drive['size'] < required_space:
            QMessageBox.warning(
                self,
                "Drive Too Small",
                f"The selected drive is too small.\n"
                f"InnovateOS requires at least {humanize.naturalsize(required_space)}."
            )
            return False
            
        # Confirm drive selection
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText("Are you sure you want to continue?")
        msg.setInformativeText(
            f"All data on drive {drive['letter']} ({drive['label']}) "
            f"will be permanently erased!"
        )
        msg.setWindowTitle("Confirm Drive Selection")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        
        if msg.exec() == QMessageBox.StandardButton.Yes:
            # Store the drive letter for the installation page
            self.setField("selected_drive", drive['letter'])
            return True
            
        return False
