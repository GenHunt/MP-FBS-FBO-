"""
Application configuration and constants
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Application info
APP_NAME = os.getenv('APP_NAME', 'Ozon FBS Label Printer')
APP_VERSION = '1.1.0'
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Ozon API
OZON_CLIENT_ID = os.getenv('OZON_CLIENT_ID', '')
OZON_API_KEY = os.getenv('OZON_API_KEY', '')
OZON_API_BASE_URL = 'https://api-seller.ozon.ru'

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = BASE_DIR / 'logs'
TEMPLATES_DIR = DATA_DIR / 'templates'
DB_PATH = DATA_DIR / 'ozon_label_printer.db'
LOG_FILE = LOGS_DIR / 'ozon_label_printer.log'

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# Printer settings
PRINTER_NAME = os.getenv('PRINTER_NAME', 'Xprinter XP-365B')
DEFAULT_PRINTER_DPI = int(os.getenv('DEFAULT_PRINTER_DPI', '203'))

# Label settings
LABEL_SIZES = {
    '58x40mm': (58, 40),
    '58x60mm': (58, 60),
    '100x150mm': (100, 150),
    '100x100mm': (100, 100),
}
DEFAULT_LABEL_SIZE = os.getenv('DEFAULT_LABEL_SIZE', '58x40mm')
DEFAULT_TEMPLATE = os.getenv('DEFAULT_TEMPLATE', 'default')

# Logging
LOG_LEVEL = 'DEBUG' if DEBUG else 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5
