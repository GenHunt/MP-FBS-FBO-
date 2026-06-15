"""
Template storage and management
"""
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from src.models.template import Template, TemplateElement, ElementType, TextAlignment
from config import TEMPLATES_DIR

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manages template storage and retrieval"""
    
    def __init__(self, templates_dir: Path = TEMPLATES_DIR):
        """
        Initialize template manager
        
        Args:
            templates_dir: Directory to store templates
        """
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        self._default_template_id = None
        self._load_default_template()
    
    def _load_default_template(self) -> None:
        """Load or create default template if it doesn't exist"""
        default_path = self.templates_dir / 'default.json'
        if not default_path.exists():
            self.create_default_template()
    
    def create_default_template(self) -> Template:
        """Create and save default template"""
        template = Template(
            template_id='default',
            name='Default Label (58x40mm)',
            label_width=58,
            label_height=40,
            description='Default label template for Ozon FBS',
            is_default=True,
        )
        
        # Add barcode element at top
        barcode_elem = TemplateElement(
            element_id='barcode_1',
            element_type=ElementType.BARCODE,
            x=5,
            y=5,
            width=48,
            height=20,
            variable='barcode',
            barcode_type='Code128',
            visible=True,
            required=True,
        )
        template.add_element(barcode_elem)
        
        # Add product name
        name_elem = TemplateElement(
            element_id='product_name',
            element_type=ElementType.TEXT,
            x=5,
            y=26,
            width=48,
            height=7,
            variable='product_name',
            font_name='Courier',
            font_size=8,
            font_bold=True,
            text_alignment=TextAlignment.CENTER,
            visible=True,
            required=True,
        )
        template.add_element(name_elem)
        
        # Add article at bottom right
        article_elem = TemplateElement(
            element_id='article',
            element_type=ElementType.TEXT,
            x=40,
            y=34,
            width=13,
            height=4,
            variable='article',
            font_name='Courier',
            font_size=7,
            text_alignment=TextAlignment.RIGHT,
            visible=True,
            required=False,
        )
        template.add_element(article_elem)
        
        self.save_template(template)
        logger.info(f"Created default template: {template.template_id}")
        return template
    
    def save_template(self, template: Template) -> bool:
        """
        Save template to file
        
        Args:
            template: Template to save
        
        Returns:
            True if successful
        """
        try:
            file_path = self.templates_dir / f'{template.template_id}.json'
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(template.to_json())
            logger.info(f"Template saved: {template.template_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save template: {e}")
            return False
    
    def load_template(self, template_id: str) -> Optional[Template]:
        """
        Load template from file
        
        Args:
            template_id: Template ID
        
        Returns:
            Template object or None
        """
        try:
            file_path = self.templates_dir / f'{template_id}.json'
            if not file_path.exists():
                logger.warning(f"Template not found: {template_id}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                template = Template.from_json(f.read())
            
            logger.info(f"Template loaded: {template_id}")
            return template
        except Exception as e:
            logger.error(f"Failed to load template: {e}")
            return None
    
    def list_templates(self) -> List[str]:
        """
        List all available templates
        
        Returns:
            List of template IDs
        """
        templates = []
        for file_path in self.templates_dir.glob('*.json'):
            template_id = file_path.stem
            templates.append(template_id)
        return sorted(templates)
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete template
        
        Args:
            template_id: Template ID
        
        Returns:
            True if successful
        """
        try:
            if template_id == 'default':
                logger.warning("Cannot delete default template")
                return False
            
            file_path = self.templates_dir / f'{template_id}.json'
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Template deleted: {template_id}")
                return True
            
            logger.warning(f"Template not found: {template_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete template: {e}")
            return False
    
    def copy_template(self, source_id: str, new_id: str, new_name: str) -> Optional[Template]:
        """
        Copy template
        
        Args:
            source_id: Source template ID
            new_id: New template ID
            new_name: New template name
        
        Returns:
            New template or None
        """
        try:
            source_template = self.load_template(source_id)
            if not source_template:
                return None
            
            # Create new template with copied data
            new_template = Template(
                template_id=new_id,
                name=new_name,
                label_width=source_template.label_width,
                label_height=source_template.label_height,
                description=f"Copy of {source_template.name}",
                is_default=False,
            )
            
            # Copy elements
            for element in source_template.elements:
                new_element = TemplateElement(
                    element_id=f"{new_id}_{element.element_id}",
                    element_type=element.element_type,
                    x=element.x,
                    y=element.y,
                    width=element.width,
                    height=element.height,
                    variable=element.variable,
                    font_name=element.font_name,
                    font_size=element.font_size,
                    font_bold=element.font_bold,
                    font_italic=element.font_italic,
                    text_alignment=element.text_alignment,
                    visible=element.visible,
                    required=element.required,
                    barcode_type=element.barcode_type,
                    meta_data=element.meta_data.copy(),
                )
                new_template.add_element(new_element)
            
            self.save_template(new_template)
            logger.info(f"Template copied: {source_id} -> {new_id}")
            return new_template
        
        except Exception as e:
            logger.error(f"Failed to copy template: {e}")
            return None
