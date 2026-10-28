"""Biblioteca con conceptos, glosario y procedimientos separados."""
import html,re,unicodedata
from PySide6.QtCore import QUrl
from PySide6.QtGui import QTextDocument
from .visual_help import diagrams_for
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QLineEdit,QListWidget,QPushButton,QComboBox,QTabWidget
from .help_content import sections
from .function_reference import function_sections
from .learning_content import concept_sections,GLOSSARY
from .report_view import ReportView,report_panel
from .cas_reference import cas_sections
from .responsive_help import ResponsiveHelpView


class TheoryPanel(QWidget):
    def __init__(self,on_open=None):
        super().__init__();self.sections=cas_sections()+function_sections()+concept_sections()+sections();self.filtered=[];self.on_open=on_open;self.selected_route=None;self.return_route=None;self.fields_open=False;self.field_route=None
        root=QHBoxLayout(self);self.body_layout=root;self.index_panel=QWidget();left=QVBoxLayout(self.index_panel);left.setContentsMargins(0,0,0,0);root.addWidget(self.index_panel,1)
        self.kind=QComboBox();self.kind.addItems(['Toda la biblioteca','Conceptos explicados','Uso de herramientas','Funciones de las fórmulas']);left.addWidget(self.kind)
        self.search=QLineEdit();self.search.setObjectName('librarySearch');self.search.setPlaceholderText('Buscar tema, herramienta o sigla…');self.search.setClearButtonEnabled(True);left.addWidget(self.search)
        self.items=QListWidget();self.items.setWordWrap(True);left.addWidget(self.items)
        self.article_panel=QWidget();right=QVBoxLayout(self.article_panel);right.setContentsMargins(0,0,0,0);root.addWidget(self.article_panel,3);actions=QHBoxLayout();right.addLayout(actions)
        self.topic_toggle=QPushButton('Buscar otro tema');self.topic_toggle.setCheckable(True);self.topic_toggle.toggled.connect(lambda *_:self.adapt_layout());actions.addWidget(self.topic_toggle)
        self.return_button=QPushButton('Volver a la herramienta');self.return_button.hide();actions.addWidget(self.return_button)
        self.open_button=QPushButton('Abrir herramienta');self.open_button.setObjectName('primary');self.open_button.setEnabled(False);self.open_button.setVisible(on_open is not None);actions.addWidget(self.open_button);actions.addStretch()
        self.open_button.clicked.connect(self.open_selected);self.return_button.clicked.connect(self.return_to_tool)
        self.text=ResponsiveHelpView();self.text.anchorClicked.connect(self.follow_reference);right.addWidget(report_panel(self.text),1)
        self.search.textChanged.connect(self.filter);self.kind.currentIndexChanged.connect(lambda *_:self.filter(self.search.text()));self.items.currentRowChanged.connect(self.show_section);self.items.itemClicked.connect(lambda *_:self.topic_toggle.setChecked(False));self.filter('');self.adapt_layout()
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,'topic_toggle'):self.adapt_layout()
    def adapt_layout(self):
        compact=self.width()<740
        self.topic_toggle.setVisible(compact)
        self.body_layout.setDirection(QHBoxLayout.Direction.TopToBottom if compact else QHBoxLayout.Direction.LeftToRight)
        self.index_panel.setVisible(not compact or self.topic_toggle.isChecked())
        self.index_panel.setMaximumHeight(180 if compact else 16777215)
        self.body_layout.setStretch(0,0 if compact else 1);self.body_layout.setStretch(1,1 if compact else 3)
    def filter(self,query):
        def norm(text):return ''.join(c for c in unicodedata.normalize('NFKD',text.casefold()) if not unicodedata.combining(c))
        words=norm(query).split();mode=self.kind.currentIndex();self.items.blockSignals(True);self.items.clear()
        self.filtered=[s for s in self.sections if (mode==0 or (mode==1 and s['route'] is None and not s.get('reference')) or (mode==2 and s['route'] is not None) or (mode==3 and s.get('reference'))) and all(word in norm(str(s)) for word in words)]
        self.items.addItems([s['category']+' · '+s['title'] for s in self.filtered]);self.items.blockSignals(False)
        if self.filtered:self.items.setCurrentRow(0)
        else:self.selected_route=None;self.open_button.setEnabled(False);self.text.setPlainText('No hay coincidencias. Probá otra palabra o elegí Toda la biblioteca.')
    def select_functions(self):
        self.search.clear();self.kind.setCurrentIndex(3);self.filter('')
    def select_tool(self,item):
        self.topic_toggle.setChecked(False)
        self.return_route=tuple(item);self.return_button.setText('Volver a '+item[0]);self.return_button.setVisible(self.on_open is not None)
        self.kind.setCurrentIndex(0);self.search.clear();self.filter('')
        for index,section in enumerate(self.filtered):
            if section['route']==tuple(item):self.items.setCurrentRow(index);return
    def show_section(self,row):
        if not 0<=row<len(self.filtered):return
        section=self.filtered[row];self.selected_route=section['route'];self.open_button.setEnabled(self.on_open is not None and self.selected_route is not None)
        blocks=list(section['blocks'])
        if self.field_route!=self.selected_route:self.fields_open=False;self.field_route=self.selected_route
        self.text._formula_number=0
        body=['<h1>'+html.escape(section['title'])+'</h1><p>'+html.escape(section['category'])+'</p>']
        illustrations=diagrams_for(section)
        def append_illustrations():
            for index,(title,picture,caption) in enumerate(illustrations):
                url=QUrl(f'help-diagram-{index}');self.text.document().addResource(QTextDocument.ResourceType.ImageResource,url,picture)
                width=min(680,max(120,self.text.viewport().width()-50));height=round(picture.height()*width/picture.width())
                body.append('<h2>'+html.escape(title)+f'</h2><img src="{url.toString()}" width="{width}" height="{height}"><p>'+html.escape(caption)+'</p>')
        for index,(title,content) in enumerate(blocks):
            body.append('<h2>'+html.escape(title)+'</h2>')
            if title=='Relación matemática':
                for line in content.splitlines():body.append(self.text._render_formula(line) or '<p>'+html.escape(line)+'</p>')
            else:
                for paragraph in content.split('\n\n'):body.append('<p style="line-height:150%">'+html.escape(paragraph).replace('\n','<br>')+'</p>')
            if index==0:append_illustrations()
        if section.get('field_reference'):
            from .library_fields import field_rows
            fields=field_rows(self.selected_route)
            body.append('<h2>Referencia de los campos</h2><p>Para consultar un dato puntual del formulario, abrí sus definiciones. La explicación de arriba muestra cómo se relacionan durante el cálculo.</p><p><a href="library:fields">'+('Ocultar definiciones' if self.fields_open else 'Ver definiciones de los campos')+'</a></p>')
            if self.fields_open:
                for name,meaning in fields:body.append('<h3>'+html.escape(name)+'</h3><p style="line-height:150%">'+html.escape(meaning)+'</p>')
            # Include the complete reference when copying/exporting the article.
            blocks.append(('Referencia de los campos','\n\n'.join(name+': '+meaning for name,meaning in fields)))
        if section.get('route') is not None or section.get('reference'):
            body.append('<p><a href="library:glossary">Consultar el glosario de siglas y términos</a></p>')
        self.text._raw=section['title']+'\n\n'+'\n\n'.join(title+'\n'+text for title,text in blocks)
        self.text._raw+='\n\n'+'\n\n'.join(title+'\n'+caption for title,_,caption in illustrations)
        self.text.setHtml('<html><body style="font-family:Segoe UI;color:#dce4ef;font-size:11pt;margin:20px">'+''.join(body)+'</body></html>')
    def follow_reference(self,url):
        if url.scheme()!='library':return
        if url.path()=='fields':
            bar=self.text.verticalScrollBar();position=bar.value();self.fields_open=not self.fields_open;self.show_section(self.items.currentRow());bar.setValue(position)
        elif url.path()=='glossary':
            self.kind.setCurrentIndex(1);self.search.setText('Glosario');self.filter('Glosario')
    def open_selected(self):
        if self.on_open and self.selected_route:self.on_open(self.selected_route)
    def return_to_tool(self):
        if self.on_open and self.return_route:self.on_open(self.return_route)
