"""Visible input methods backed by existing combo-box state and signals."""
from PySide6.QtWidgets import QWidget,QHBoxLayout,QToolButton,QButtonGroup,QSizePolicy
class ChoiceButtons(QWidget):
    def __init__(self,combo,labels=None):
        super().__init__();self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed);self.combo=combo;combo.setParent(self);self.labels=labels;self.buttons=[]
        row=QHBoxLayout(self);row.setContentsMargins(0,0,0,0);row.setSpacing(4);self.group=QButtonGroup(self);self.group.setExclusive(True)
        for index in range(combo.count()):
            button=QToolButton();button.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed);button.setCheckable(True);button.setProperty('segment',True);button.setAccessibleName((labels[index] if labels else combo.itemText(index)));self.group.addButton(button,index);self.buttons.append(button);row.addWidget(button,1)
        self.group.idClicked.connect(combo.setCurrentIndex);combo.currentIndexChanged.connect(self.refresh);combo.model().dataChanged.connect(self.refresh);combo.hide();self.refresh()
    def refresh(self,*_):
        for index,button in enumerate(self.buttons):button.setText(self.labels[index] if self.labels else self.combo.itemText(index));button.setChecked(index==self.combo.currentIndex())
