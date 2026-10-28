"""A public problem owns its variants, inputs and results in one document."""
from PySide6.QtWidgets import QWidget,QVBoxLayout
from .active_stack import ActiveStack

def document_route(entry):return (entry['title'],'workspace',entry['key'],None)

class ProblemDocument(QWidget):
    def __init__(self,entry):
        super().__init__();self.entry=entry;self.pages={};self.current_page=None;self.current_route=None
        root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0);self.stack=ActiveStack();root.addWidget(self.stack)
    def select_page(self,page):
        route=page.tool_item
        if route not in self.pages:self.pages[route]=page;self.stack.addWidget(page)
        self.current_page=page;self.current_route=route;self.stack.setCurrentWidget(page);self.stack.updateGeometry()
