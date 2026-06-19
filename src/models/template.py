"""
Template and template elements models
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from enum import Enum
import json


class ElementType(Enum):
    """Types of elements in a template"""
    TEXT = "text"
    BARCODE = "barcode"
    IMAGE = "image"
    LINE = "line"


class PrintType(Enum):
    """Print type options"""
    ROUTING = "routing"
    INTERNAL = "internal"
    BOTH = "both"


class TextAlignment(Enum):
    """Text alignment options"""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


@dataclass
class TemplateElement:
    """Represents a single element in a label template"""
    element_id: str
    element_type: ElementType
    x: float  # X coordinate in mm
    y: float  # Y coordinate in mm
    width: float  # Width in mm
    height: float  # Height in mm
    variable: Optional[str] = None  # Reference to data variable (e.g., 'article', 'product_name')
    font_name: str = "Courier"
    font_size: int = 12
    font_bold: bool = False
    font_italic: bool = False
    text_alignment: TextAlignment = TextAlignment.LEFT
    visible: bool = True
    required: bool = True
    barcode_type: str = "Code128"  # For barcode elements
    meta_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert element to dictionary"""
        return {
            'element_id': self.element_id,
            'element_type': self.element_type.value,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'variable': self.variable,
            'font_name': self.font_name,
            'font_size': self.font_size,
            'font_bold': self.font_bold,
            'font_italic': self.font_italic,
            'text_alignment': self.text_alignment.value,
            'visible': self.visible,
            'required': self.required,
            'barcode_type': self.barcode_type,
            'meta_data': self.meta_data,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateElement':
        """Create element from dictionary"""
        data_copy = data.copy()
        data_copy['element_type'] = ElementType(data_copy['element_type'])
        data_copy['text_alignment'] = TextAlignment(data_copy['text_alignment'])
        return cls(**data_copy)


@dataclass
class Template:
    """Represents a label template"""
    template_id: str
    name: str
    label_width: float  # Width in mm
    label_height: float  # Height in mm
    elements: List[TemplateElement] = field(default_factory=list)
    description: str = ""
    is_default: bool = False
    created_at: str = ""
    updated_at: str = ""
    meta_data: Dict[str, Any] = field(default_factory=dict)
    
    def add_element(self, element: TemplateElement) -> None:
        """Add element to template"""
        self.elements.append(element)
    
    def remove_element(self, element_id: str) -> bool:
        """Remove element from template by ID"""
        self.elements = [e for e in self.elements if e.element_id != element_id]
        return True
    
    def get_element(self, element_id: str) -> Optional[TemplateElement]:
        """Get element by ID"""
        for element in self.elements:
            if element.element_id == element_id:
                return element
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary"""
        return {
            'template_id': self.template_id,
            'name': self.name,
            'label_width': self.label_width,
            'label_height': self.label_height,
            'elements': [e.to_dict() for e in self.elements],
            'description': self.description,
            'is_default': self.is_default,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'meta_data': self.meta_data,
        }
    
    def to_json(self) -> str:
        """Convert template to JSON string"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Template':
        """Create template from dictionary"""
        data_copy = data.copy()
        elements_data = data_copy.pop('elements', [])
        template = cls(**data_copy)
        template.elements = [TemplateElement.from_dict(e) for e in elements_data]
        return template
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Template':
        """Create template from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def __repr__(self) -> str:
        return f"Template(id={self.template_id}, name={self.name}, elements={len(self.elements)})"
