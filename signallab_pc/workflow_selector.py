"""Visible problem variants, with compatible local inputs carried between views."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QFormLayout,QComboBox,QHBoxLayout,QLabel,QToolButton,QButtonGroup,QSizePolicy
from .tool_catalog import normalized_key
from .workflow_inputs import copy_inputs,prepare_inputs
import html
class WorkflowSelector(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.entry=None;self.current_key=None;self.memory={};self.rows=[]
        self.form=QFormLayout(self);self.form.setContentsMargins(10,3,10,7);self.form.setVerticalSpacing(5);self.form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows);self.hide()
    def set_entry(self,entry,item):
        key=normalized_key(item);self.memory[entry['key']]=key
        if self.entry is entry and self.current_key==key:
            self.setVisible(self.form.rowCount()>0);return
        self.entry=entry;self.current_key=key
        while self.form.rowCount():
            row=self.form.takeRow(0)
            for item in (row.labelItem,row.fieldItem):
                if item is not None and item.widget() is not None:item.widget().hide();item.widget().deleteLater()
        self.rows=[];variants=entry['variants'];selected=next((values for candidate,values in variants if candidate==key),variants[0][1]);prefix=()
        for index,label in enumerate(entry['dimensions']):
            values=list(dict.fromkeys(values[index] for _,values in variants if values[:index]==prefix))
            current=selected[index];prefix=prefix+(current,)
            if len(values)<2:continue
            if len(values)<=3 and max(map(len,values))<=26:
                row=QWidget();layout=QHBoxLayout(row);layout.setContentsMargins(0,0,0,0);layout.setSpacing(4);group=QButtonGroup(row)
                for value in values:
                    button=QToolButton();button.setSizePolicy(QSizePolicy.Policy.Preferred,QSizePolicy.Policy.Fixed);button.setText(value);button.setCheckable(True);button.setChecked(value==current);button.setProperty('segment',True);button.setToolTip('Evalúa un registro finito; sus muestras pueden definirse mediante una fórmula.' if value=='Numérico' else 'Trabaja con una expresión y su soporte; conserva las condiciones del cálculo.' if value=='Algebraico' else value);group.addButton(button);layout.addWidget(button)
                    button.clicked.connect(lambda checked=False,i=index,v=value:self.select(i,v))
                layout.addStretch();self.form.addRow(label,row)
            else:
                combo=QComboBox();combo.addItems(values);combo.setCurrentText(current);combo.setAccessibleName(label);combo.textActivated.connect(lambda value,i=index:self.select(i,value));self.form.addRow(label,combo)
        self.setVisible(self.form.rowCount()>0)
    def select(self,index,value):
        entry=self.entry;variants=entry['variants'];old=next(values for key,values in variants if key==self.current_key);prefix=old[:index]+(value,)
        candidates=[(key,values) for key,values in variants if values[:index+1]==prefix]
        # Keep compatible later choices when changing an earlier dimension.
        key,values=max(candidates,key=lambda item:sum(a==b for a,b in zip(item[1][index+1:],old[index+1:])))
        source=self.window.pages.get(self.window.current_operation)
        route=self.window.route_for_key(key);existed=route in self.window.pages
        self.window.open_tool(route)
        target=self.window.pages.get(self.window.current_operation)
        if source is not None and target is not None and source is not target:
            plan=prepare_inputs(source,target)
            label=QLabel();label.setWordWrap(True);label.setObjectName('muted');self.form.addRow(label)
            if not existed:label.setText(plan.apply())
            elif plan.actions:
                origin=' · '.join(old);label.setText('Se conservó la entrada de esta vista. <a href="copy">Copiar entrada de '+html.escape(origin)+'</a>')
                def apply_copy(*_):
                    label.setText(prepare_inputs(source,target).apply())
                label.linkActivated.connect(apply_copy)
            else:label.setText(plan.note)