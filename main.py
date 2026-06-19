"""
main.py - Application entry point for Ozon FBS Label Printer
"""
import sys
import logging
import logging.handlers
from pathlib import Path


def setup_logging():
    """Configure application logging"""
    import config

    log_dir = config.LOGS_DIR
    log_dir.mkdir(exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))

    formatter = logging.Formatter(config.LOG_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            config.LOG_FILE,
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT,
            encoding='utf-8',
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: could not create log file handler: {e}")


def main():
    """Application entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Ozon FBS Label Printer")

    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt

        app = QApplication(sys.argv)
        app.setApplicationName("Ozon FBS Label Printer")
        app.setApplicationVersion("1.1.0")

        from src.ui.main_window import MainWindow

        window = MainWindow()
        window.show()

        logger.info("Application started successfully")
        sys.exit(app.exec())

    except ImportError as e:
        logger.critical(f"Failed to import required module: {e}")
        print(f"Error: Missing required module - {e}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Application crashed: {e}", exc_info=True)
        print(f"Critical error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
