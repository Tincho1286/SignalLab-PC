"""Sparse sample patches and field edits; applied outputs remain independent."""
import time
import numpy as np
from PySide6.QtGui import QUndoCommand,QUndoStack


class Edit(QUndoCommand):
    def __init__(self,history,key,before,after,title):
        super().__init__(title);self.history=history;self.key=key;self.before=before;self.after=after;self.when=time.monotonic();self.epoch=history.epoch
    def id(self):return 1 if isinstance(self.key,str) else -1
    def mergeWith(self,other):
        if self.key!=other.key or self.epoch!=other.epoch or other.when-self.when>1:return False
        self.after=other.after;self.when=other.when;return True
    def redo(self):self.history.apply(self.key,self.after)
    def undo(self):self.history.apply(self.key,self.before)


class History:
    def __init__(self,panel):self.panel=panel;self.stack=QUndoStack(panel);self.baseline=None;self.fields={};self.epoch=0
    def reset(self):self.stack.clear();self.checkpoint()
    def checkpoint(self):
        p=self.panel;self.baseline=p.current.values.copy();self.fields={key:getattr(p,key).text() for key in ('name','origin','step')};self.last_fields=dict(self.fields);self.epoch+=1
    def refresh(self):
        p=self.panel;p.pending=bool(p.changed_rows) or any(getattr(p,key).text()!=value for key,value in self.fields.items());p.update_buttons()
    def field_changed(self):
        p=self.panel
        for key in self.fields:
            value=getattr(p,key).text();before=self.last_fields[key]
            if value!=before:self.stack.push(Edit(self,key,before,value,'Cambiar '+key));return
    def values(self,indices,values):
        indices=np.asarray(indices,dtype=np.int64);values=np.asarray(values,dtype=complex)
        if values.shape!=indices.shape or not np.all(np.isfinite(values)):raise ValueError('La edición requiere una muestra finita por fila.')
        if np.any(indices<0) or np.any(indices>=len(self.panel.current.values)):raise ValueError('La edición excede el registro.')
        mask=self.panel.current.values[indices]!=values
        if np.any(mask):self.stack.push(Edit(self,tuple(int(i) for i in indices[mask]),self.panel.current.values[indices[mask]].copy(),values[mask].copy(),'Editar muestras'))
    def apply(self,key,value):
        p=self.panel
        if isinstance(key,str):
            p._setting_fields=True
            try:getattr(p,key).setText(value);self.last_fields[key]=value
            finally:p._setting_fields=False
        else:
            indices=np.asarray(key,dtype=np.int64);p.current.values[indices]=value
            for i in indices:
                if p.current.values[i]==self.baseline[i]:p.changed_rows.discard(int(i))
                else:p.changed_rows.add(int(i))
        self.refresh();p.render()
