"""
Модель шаблона внутренней этикетки.
Формат хранения: JSON. Размер по умолчанию: 58×40 мм.
"""
from __future__ import annotations
import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Literal


ElementType = Literal["text", "barcode"]
AlignType = Literal["left", "center", "right"]


@dataclass
class TemplateElement:
    """Один элемент шаблона (текст или штрихкод)."""
    type: ElementType = "text"          # text | barcode
    x_mm: float = 1.0
    y_mm: float = 1.0
    w_mm: float = 50.0
    h_mm: float = 8.0
    variable: str = ""                  # имя переменной LabelContext или ""
    static_text: str = ""              # статический текст (если variable пуст)
    font_family: str = "Helvetica"
    font_size: float = 8.0
    bold: bool = False
    align: AlignType = "left"
    visible: bool = True
    required: bool = False             # если True и значение пустое — предупреждать

    def get_text(self, ctx_getter) -> str:
        """Получить текст для отображения."""
        if self.variable:
            val = ctx_getter(self.variable)
            return val if val else self.static_text
        return self.static_text

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "TemplateElement":
        allowed = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in allowed}
        return cls(**filtered)


@dataclass
class Template:
    """Шаблон этикетки."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Новый шаблон"
    width_mm: float = 58.0
    height_mm: float = 40.0
    default: bool = False
    elements: List[TemplateElement] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "name": self.name,
            "width_mm": self.width_mm,
            "height_mm": self.height_mm,
            "default": self.default,
            "elements": [e.to_dict() for e in self.elements],
        }
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Template":
        elements = [TemplateElement.from_dict(e) for e in d.get("elements", [])]
        return cls(
            id=d.get("id", str(uuid.uuid4())),
            name=d.get("name", "Шаблон"),
            width_mm=float(d.get("width_mm", 58.0)),
            height_mm=float(d.get("height_mm", 40.0)),
            default=bool(d.get("default", False)),
            elements=elements,
        )

    def copy(self) -> "Template":
        import copy
        t = copy.deepcopy(self)
        t.id = str(uuid.uuid4())
        t.name = f"{self.name} (копия)"
        t.default = False
        return t


def default_template() -> Template:
    """Базовый шаблон 58×40 мм с штрихкодом, наименованием, артикулом и номером отправления."""
    elements = [
        # Штрихкод
        TemplateElement(
            type="barcode",
            x_mm=3.0, y_mm=2.0, w_mm=52.0, h_mm=14.0,
            variable="barcode",
            static_text="0000000000000",
            visible=True,
            required=False,
        ),
        # Наименование товара
        TemplateElement(
            type="text",
            x_mm=1.0, y_mm=18.0, w_mm=56.0, h_mm=10.0,
            variable="product_name",
            font_size=7.0,
            align="left",
            visible=True,
            required=True,
        ),
        # Артикул (внизу справа)
        TemplateElement(
            type="text",
            x_mm=30.0, y_mm=33.0, w_mm=27.0, h_mm=5.0,
            variable="article",
            font_size=7.0,
            bold=True,
            align="right",
            visible=True,
            required=False,
        ),
        # Номер отправления
        TemplateElement(
            type="text",
            x_mm=1.0, y_mm=33.0, w_mm=28.0, h_mm=5.0,
            variable="posting_number",
            font_size=6.0,
            align="left",
            visible=True,
            required=False,
        ),
        # Количество
        TemplateElement(
            type="text",
            x_mm=1.0, y_mm=29.0, w_mm=56.0, h_mm=4.5,
            variable="quantity",
            static_text="",
            font_size=6.5,
            align="left",
            visible=True,
            required=False,
        ),
    ]
    return Template(
        name="Стандарт 58×40",
        width_mm=58.0,
        height_mm=40.0,
        default=True,
        elements=elements,
    )


def load_templates(path: str) -> List[Template]:
    """Загрузить шаблоны из JSON-файла."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Template.from_dict(d) for d in data]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return [default_template()]


def save_templates(path: str, templates: List[Template]) -> None:
    """Сохранить шаблоны в JSON-файл."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump([t.to_dict() for t in templates], f, ensure_ascii=False, indent=2)
