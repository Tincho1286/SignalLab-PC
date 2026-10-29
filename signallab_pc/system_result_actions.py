"""Consistent actions on the calculated system, never on uncalculated form edits."""
from PySide6.QtWidgets import QWidget,QHBoxLayout,QPushButton,QMenu
from .workspaces import ROUTES

class SystemResultActions(QWidget):
    def __init__(self,window):
        super().__init__();self.owner=window;self.system=None;self.key=None;self.reuse_excluded=set();row=QHBoxLayout(self);row.setContentsMargins(0,0,0,0)
        self.analysis=QPushButton('Analizar…');self.analysis.setProperty('actionRole','analysis');menu=QMenu(self.analysis);self.analysis.setMenu(menu)
        menu.addAction('Polos y ceros',self.roots)
        menu.addAction('Respuesta en frecuencia',lambda:self.send_to(('system_analysis',0)))
        self.temporal_action=menu.addAction('Respuesta temporal',lambda:self.send_to(('systems',9)))
        row.addWidget(self.analysis)
        self.reuse=QPushButton('Usar filtro en…');self.reuse.setProperty('actionRole','reuse');self.reuse_menu=QMenu(self.reuse);self.reuse.setMenu(self.reuse_menu);self.reuse_menu.aboutToShow.connect(self.prepare_reuse);row.addWidget(self.reuse)
        self.export_button=QPushButton('Exportar filtro…');self.export_button.clicked.connect(lambda:self.owner.export_transfer(self.system) if self.system is not None else None);row.addWidget(self.export_button)
        self.set_result(None)
    def set_result(self,system,key=None):
        self.system=system;self.key=key;self.setEnabled(system is not None)
        for button in (self.analysis,self.reuse,self.export_button):button.setEnabled(system is not None)
        self.temporal_action.setEnabled(system is not None and not system.advance)
        self.temporal_action.setToolTip('Para un sistema con avance, usá Z inversa con ROC y un intervalo de índices.' if system is not None and system.advance else '')
    def send_to(self,key):
        if self.system is not None:self.owner.send_system(self.system,self.key,ROUTES[key])
    def roots(self):
        if self.system is not None:self.owner.open_root_analysis(self.system,self.key)
    def prepare_reuse(self):
        self.reuse_menu.clear()
        if self.system is None:return
        from .cas_transfer import send_to_cas
        self.reuse_menu.addAction('Calculadora CAS',lambda:send_to_cas(self.owner,self.key,value=self.system));self.reuse_menu.addSeparator()
        from .toolbox import system_destinations
        from .tool_catalog import compact_destinations,AREA_BY_ID,normalized_key,destination_label
        from .navigation import MENUS
        groups={};self.menu_refs=[]
        items=[item for item in system_destinations(self.system,[item for group in MENUS.values() for item in group]) if item[1:3] not in self.reuse_excluded]
        for entry,item in compact_destinations(items):
            area=entry['area']
            if area not in groups:groups[area]=self.reuse_menu.addMenu(AREA_BY_ID[area][1]);self.menu_refs.append(groups[area])
            available={normalized_key(candidate):candidate for candidate in items}
            variants=[(available[key],values) for key,values in entry['variants'] if key in available]
            if len(variants)>1:
                submenu=groups[area].addMenu(entry['title']);self.menu_refs.append(submenu)
                for route,values in variants:submenu.addAction(' · '.join(values),lambda checked=False,target=route:self.owner.send_system(self.system,self.key,target))
            else:
                label='Respuesta temporal' if item[1:3]==('systems',9) else destination_label(entry,item)
                groups[area].addAction(label,lambda checked=False,route=item:self.owner.send_system(self.system,self.key,route))
