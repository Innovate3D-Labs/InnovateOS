import logging
from PyQt6.QtWidgets import QWizard
from PyQt6.QtCore import Qt
from .pages import WelcomePage, DrivePage, ConfigPage, InstallPage, FinishPage
from utils.installer import InstallerManager

class InstallerWindow(QWizard):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.installer = InstallerManager()
        self.setWindowTitle("InnovateOS Installer")
        
        # Set window properties
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.NoBackButtonOnStartPage)
        self.setOption(QWizard.WizardOption.NoBackButtonOnLastPage)
        self.setOption(QWizard.WizardOption.NoCancelButtonOnLastPage)
        
        # Set minimum size
        self.setMinimumSize(600, 400)
        
        # Add pages
        self.welcome_page = WelcomePage()
        self.drive_page = DrivePage()
        self.config_page = ConfigPage()
        self.install_page = InstallPage()
        self.finish_page = FinishPage()
        
        self.addPage(self.welcome_page)
        self.addPage(self.drive_page)
        self.addPage(self.config_page)
        self.addPage(self.install_page)
        self.addPage(self.finish_page)
        
        # Set button text
        self.setButtonText(QWizard.WizardButton.NextButton, "Next")
        self.setButtonText(QWizard.WizardButton.BackButton, "Back")
        self.setButtonText(QWizard.WizardButton.FinishButton, "Finish")
        self.setButtonText(QWizard.WizardButton.CancelButton, "Cancel")
        
    def closeEvent(self, event):
        """Handle window close event"""
        # Clean up any temporary files
        if hasattr(self, 'install_page'):
            if hasattr(self.install_page, 'installer'):
                self.install_page.installer.cleanup()
        event.accept()
