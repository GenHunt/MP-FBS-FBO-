# -*- coding: utf-8 -*-
"""
Application configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root
PROJECT_ROOT = Path(__file__).parent

# Directories
DATA_DIR = PROJECT_ROOT / 'data'
LOGS_DIR = PROJECT_ROOT / 'logs'
TEMPLATES_DIR = DATA_DIR / 'templates'
DATABASE_DIR = DATA_DIR

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# Database
DATABASE_PATH = DATABASE_DIR / 'ozon_label_printer.db'

# Logging
LOG_FILE = LOGS_DIR / 'ozon_label_printer.log'
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Application
APP_NAME = 'Ozon FBS Label Printer'
APP_VERSION = '1.1.0'
APP_AUTHOR = 'GenHunt'

# API Configuration
OZON_CLIENT_ID = os.getenv('OZON_CLIENT_ID', '')
OZON_API_KEY = os.getenv('OZON_API_KEY', '')
OZON_API_URL = 'https://api.ozon.ru'

# Printer Configuration
PRINTER_NAME = os.getenv('PRINTER_NAME', 'Xprinter XP-365B')
DEFAULT_PRINTER_DPI = int(os.getenv('DEFAULT_PRINTER_DPI', '203'))

# Label Configuration
DEFAULT_LABEL_SIZE = os.getenv('DEFAULT_LABEL_SIZE', '58x40')
DEFAULT_TEMPLATE = os.getenv('DEFAULT_TEMPLATE', 'default')

LABEL_SIZES = {
    '58x40': {'width': 58, 'height': 40},
    '60x40': {'width': 60, 'height': 40},
    '80x50': {'width': 80, 'height': 50},
    '100x150': {'width': 100, 'height': 150},
}

# UI Configuration
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
WINDOW_TITLE = f'{APP_NAME} v{APP_VERSION}'

# Request Configuration
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
