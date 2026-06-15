"""
Printer management module for Windows printer integration
"""
import logging
import subprocess
from typing import List, Optional
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)


class PrinterManager:
    """Manages printing to Windows printers"""
    
    @staticmethod
    def get_installed_printers() -> List[str]:
        """Get list of installed printers"""
        try:
            result = subprocess.run(
                ['powershell', '-Command', 'Get-Printer | Select-Object -ExpandProperty Name'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                printers = [p.strip() for p in result.stdout.strip().split('\n') if p.strip()]
                logger.info(f"Found {len(printers)} printers")
                return printers
            else:
                logger.warning("Failed to get printer list")
                return []
        
        except Exception as e:
            logger.error(f"Failed to get printers: {e}")
            return []
    
    @staticmethod
    def print_image(image_path: str, printer_name: str, dpi: int = 203) -> bool:
        """
        Print image to Windows printer
        
        Args:
            image_path: Path to image file
            printer_name: Printer name
            dpi: Print DPI
        
        Returns:
            True if successful
        """
        try:
            # Use Windows Print Dialog
            result = subprocess.run(
                [
                    'powershell', '-Command',
                    f'Add-Type -AssemblyName System.Drawing; '
                    f'$img = [System.Drawing.Image]::FromFile("{image_path}"); '
                    f'$pd = New-Object System.Drawing.Printing.PrintDocument; '
                    f'$pd.PrinterSettings.PrinterName = "{printer_name}"; '
                    f'$pd.Print()'
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"Image printed successfully to {printer_name}")
                return True
            else:
                logger.error(f"Print failed: {result.stderr}")
                return False
        
        except Exception as e:
            logger.error(f"Failed to print image: {e}")
            return False
    
    @staticmethod
    def print_pdf(pdf_path: str, printer_name: str) -> bool:
        """
        Print PDF to Windows printer
        
        Args:
            pdf_path: Path to PDF file
            printer_name: Printer name
        
        Returns:
            True if successful
        """
        try:
            # Try using SumatraPDF if available
            result = subprocess.run(
                [
                    'powershell', '-Command',
                    f'& "C:\\Program Files\\SumatraPDF\\SumatraPDF.exe" '
                    f'-print-to "{printer_name}" "{pdf_path}"'
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"PDF printed successfully to {printer_name}")
                return True
            
            # Fallback to Windows Print function
            result = subprocess.run(
                [
                    'powershell', '-Command',
                    f'Start-Process -FilePath "{pdf_path}" '
                    f'-Verb PrintTo -ArgumentList "{printer_name}"'
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"PDF printed with fallback method to {printer_name}")
                return True
            
            logger.error(f"Print failed: {result.stderr}")
            return False
        
        except Exception as e:
            logger.error(f"Failed to print PDF: {e}")
            return False
    
    @staticmethod
    def test_printer(printer_name: str) -> bool:
        """
        Test if printer is available
        
        Args:
            printer_name: Printer name
        
        Returns:
            True if printer is available
        """
        try:
            printers = PrinterManager.get_installed_printers()
            is_available = printer_name in printers
            
            if is_available:
                logger.info(f"Printer '{printer_name}' is available")
            else:
                logger.warning(f"Printer '{printer_name}' is not available")
            
            return is_available
        
        except Exception as e:
            logger.error(f"Failed to test printer: {e}")
            return False
