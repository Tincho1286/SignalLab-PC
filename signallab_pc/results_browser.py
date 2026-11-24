"""Saved results use the same selection, detail and action positions as tools."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QLineEdit,QComboBox,QCheckBox,QListWidget,QPushButton,QMenu,QSizePolicy
from .tool_workspace import ToolWorkspace
from .result_toolbar import ResultActionBar
from .report_view import ReportView


class ResultsBrowser(QWidget):
    def __init__(self,window):
        super().__init__();root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0)
        selection=QWidget();left=QVBoxLayout(selection);left.setContentsMargins(0,0,0,0);left.setSpacing(9)
        window.result_search=QLineEdit();window.result_search.setAccessibleName('Buscar resultados');window.result_search.setPlaceholderText('Nombre u operación…');window.result_search.setClearButtonEnabled(True);left.addWidget(window.result_search)
        window.result_kind=QComboBox();window.result_kind.setAccessibleName('Tipo de resultado');window.result_kind.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Fixed)
        for label,kind in [('Todos los tipos',None),('Señales','signal'),('Sistemas','system'),('Modelos de estados','state_space'),('Expresiones','expression'),('Cálculos e informes','calculation')]:window.result_kind.addItem(label,kind)
        left.addWidget(window.result_kind);window.include_inputs=QCheckBox('Incluir las entradas utilizadas');left.addWidget(window.include_inputs)
        window.result_count=QLabel();window.result_count.setObjectName('muted');left.addWidget(window.result_count)
        window.project_list=QListWidget();window.project_list.setObjectName('savedResults');window.project_list.setAccessibleName('Resultados guardados');window.project_list.setWordWrap(True);window.project_list.setMinimumHeight(160);left.addWidget(window.project_list,1)
        detail=QWidget();right=QVBoxLayout(detail);right.setContentsMargins(0,0,0,0);right.setSpacing(10);self.actions=ResultActionBar();right.addWidget(self.actions)
        window.view_selection=QPushButton('Abrir resultado');window.view_selection.setEnabled(False);window.view_selection.clicked.connect(window.open_selected_signal);self.actions.add_action(window.view_selection,'graph')
        window.reuse_selection=QPushButton('Usar resultado en…');window.reuse_selection.setEnabled(False);window.reuse_menu=QMenu(window.reuse_selection);window.reuse_selection.setMenu(window.reuse_menu);window.reuse_menu.aboutToShow.connect(window.prepare_selected_reuse);self.actions.add_action(window.reuse_selection,'reuse')
        window.cas_selection=QPushButton('Enviar a CAS');window.cas_selection.setEnabled(False);window.cas_selection.clicked.connect(self.send_cas);self.actions.add_action(window.cas_selection,'cas')
        window.export_selection_button=QPushButton('Exportar resultado…');window.export_selection_button.setEnabled(False);window.export_selection_button.clicked.connect(window.export_selected);self.actions.add_action(window.export_selection_button,'export')
        from .result_comparison import open_comparison
        compare=QPushButton('Comparar resultados…');compare.clicked.connect(lambda:open_comparison(window));self.actions.add_action(compare)
        sessions = QPushButton('Sesión…')
        self.session_menu = QMenu(sessions)
        populate = getattr(window, 'populate_session_menu', None)
        if populate is None:
            self.session_menu.addAction('Guardar resultados…', window.save_project)
            self.session_menu.addAction('Incorporar resultados…', window.import_project)
        else:
            populate(self.session_menu)
        sessions.setMenu(self.session_menu)
        self.actions.add_action(sessions)
        window.result_origin=QLabel();window.result_origin.setWordWrap(True);window.result_origin.setObjectName('muted');right.addWidget(window.result_origin)
        window.project_details=ReportView();window.project_details.setReadOnly(True);window.project_details.setMinimumHeight(180);right.addWidget(window.project_details,1)
        self.workspace=ToolWorkspace(selection,detail,self,titles=('Resultados','Detalle'),captions=('Elegí un cálculo guardado. Los más recientes aparecen primero.','Consultá el resultado y sus condiciones antes de reutilizarlo.'));root.addWidget(self.workspace)
        self.window_owner=window;window.result_search.textChanged.connect(window.refresh_project);window.result_kind.currentIndexChanged.connect(window.refresh_project);window.include_inputs.toggled.connect(window.refresh_project);window.project_list.currentRowChanged.connect(window.show_record);window.project_list.itemDoubleClicked.connect(lambda *_:window.open_selected_signal());window.refresh_project()

    def send_cas(self):
        window=self.window_owner;index=window.project_list.currentRow()
        if 0<=index<len(window.visible_records):
            from .cas_transfer import send_to_cas
            send_to_cas(window,window.visible_records[index]['id'])
