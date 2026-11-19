"""Contextual model destinations join the standard reuse menu."""
from PySide6.QtCore import QObject,QEvent
from PySide6.QtWidgets import QAbstractButton


class ContextReuse(QObject):
    def __init__(self,surface):super().__init__(surface);self.surface=surface;self.sources=[];self.connected=set()
    def eventFilter(self,watched,event):
        if event.type() in (QEvent.Type.Show,QEvent.Type.ShowToParent):watched.hide()
        return False
    def install(self,dock):
        for button in self.surface.content.findChildren(QAbstractButton):
            if button.property('resultReuseMenu') and button not in self.sources:self.sources.append(button);button.setProperty('resultReuseCaptured',True);button.installEventFilter(self);button.hide()
        for bar,_,_ in dock.entries:
            button=bar.slots.get('reuse');menu=button.menu() if button is not None else None
            if menu is not None and bar.property('systemResultActions') and menu not in self.connected:
                self.connected.add(menu);menu.aboutToShow.connect(lambda target=menu:self.append(target))
    def append(self,menu):
        exports=self.surface.result_exports
        for button in self.sources:
            if button.menu() is not None and exports.path(button.parentWidget()) is not None:
                menu.addSeparator();action=menu.addMenu(button.menu());action.setText(button.property('resultReuseMenu'));action.setEnabled(button.isEnabled());action.setToolTip(button.toolTip())


def install(surface,dock):
    commands=getattr(surface,'context_reuse',None)
    if commands is None:commands=ContextReuse(surface);surface.context_reuse=commands
    commands.install(dock)
