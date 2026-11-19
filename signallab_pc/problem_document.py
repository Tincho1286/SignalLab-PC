"""A public problem owns its variants, inputs and results in one document."""
from PySide6.QtWidgets import QWidget,QVBoxLayout
from .active_stack import ActiveStack

def document_route(entry):return (entry['title'],'workspace',entry['key'],None)

class ProblemDocument(QWidget):
    def __init__(self,entry):
        super().__init__();self.entry=entry;self.pages={};self.current_page=None;self.current_route=None
        root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0);self.stack=ActiveStack();root.addWidget(self.stack)
    def hasHeightForWidth(self):return True
    def heightForWidth(self,width):
        # The header wraps, but the workspace's scrollable surfaces can shrink.
        # Its preferred 620px height must not become the scroll document's floor.
        layout=self.layout();margins=layout.contentsMargins();inner=max(0,width-margins.left()-margins.right());heights=[]
        for index in range(layout.count()):
            widget=layout.itemAt(index).widget()
            if widget is None or widget.isHidden():continue
            if widget is self.stack:height=widget.minimumSizeHint().height()
            else:height=widget.heightForWidth(inner) if widget.hasHeightForWidth() else widget.sizeHint().height()
            heights.append(max(0,height))
        return margins.top()+margins.bottom()+sum(heights)+max(0,len(heights)-1)*layout.spacing()
    def select_page(self,page):
        route=page.tool_item
        if route not in self.pages:self.pages[route]=page;self.stack.addWidget(page)
        self.current_page=page;self.current_route=route;self.stack.setCurrentWidget(page);self.stack.updateGeometry()
