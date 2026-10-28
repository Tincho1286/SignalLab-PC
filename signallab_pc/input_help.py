"""Ayuda de parámetros desplegable sin abandonar la herramienta."""
import html
from PySide6.QtWidgets import QWidget,QVBoxLayout,QPushButton
from .report_view import ReportView
from .tool_help_catalog import GUIDES
from .visual_help import parameter_blocks

class InputHelp(QWidget):
    def __init__(self,item):
        super().__init__();layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        self.button=QPushButton('Qué cargar y cómo interpretar el resultado');self.button.setCheckable(True);layout.addWidget(self.button)
        self.text=ReportView();self.text.setMinimumHeight(180);self.text.setMaximumHeight(250);self.text.hide();layout.addWidget(self.text)
        section={'route':item};blocks=parameter_blocks(section)
        body=''.join('<h3>'+html.escape(title)+'</h3>'+''.join('<p>'+html.escape(line)+'</p>' for line in content.splitlines()) for title,content in blocks)
        self.text.setHtml('<body style="color:#dce4ef;font-family:Segoe UI">'+body+'</body>')
        self.button.toggled.connect(self.text.setVisible)
