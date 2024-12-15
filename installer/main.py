import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from ui.main_window import InstallerWindow

def setup_logging():
    """Set up logging configuration"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "installer.log"),
            logging.StreamHandler()
        ]
    )

def main():
    """Main entry point for the installer"""
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting InnovateOS Installer")
    
    try:
        # Create Qt application
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # Modern style
        
        # Create and show main window
        window = InstallerWindow()
        window.show()
        
        # Start event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Error starting installer: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
