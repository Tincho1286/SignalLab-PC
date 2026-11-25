"""Biblioteca con conceptos, glosario y procedimientos separados."""
import html
from PySide6.QtCore import QTimer,QUrl,Qt
from PySide6.QtGui import QCursor,QTextDocument
from .visual_help import diagrams_for
from PySide6.QtWidgets import QApplication,QComboBox,QLabel,QLineEdit,QMenu,QPushButton,QSplitter,QToolButton,QToolTip,QTreeWidget,QTreeWidgetItem,QVBoxLayout,QWidget
from .library_catalog import sections as library_sections
from .library_titles import TOPICS
from .responsive_help import ResponsiveHelpView
from .tool_catalog import normalize
from .wrapping_row import WrappingRow


KINDS = ('', 'concept', 'tool', 'reference', 'example')
KIND_LABELS = {'concept': 'Concepto', 'tool': 'Guía', 'reference': 'Referencia', 'example': 'Ejemplo'}


class TheoryPanel(QWidget):
    def __init__(self,on_open=None,on_example=None):
        super().__init__();self.on_example=on_example;self.sections=library_sections();self.filtered=[];self.on_open=on_open;self.selected_route=None;self.return_route=None
        self.guide_context = None
        self.guide_anchors = {}
        self.search_index = [self.search_entry(section) for section in self.sections]
        self.last_query = ''
        self.compact = None
        self.split_sizes = [310, 740]
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 0, 14, 12)
        root.setSpacing(8)
        action_row = WrappingRow()
        root.addWidget(action_row)
        self.return_button = QPushButton('Volver al cálculo')
        self.return_button.hide()
        self.return_button.clicked.connect(self.return_to_tool)
        action_row.flow.addWidget(self.return_button)
        self.topic_toggle = QPushButton('Catálogo')
        self.topic_toggle.setCheckable(True)
        self.topic_toggle.toggled.connect(self.toggle_catalog)
        action_row.flow.addWidget(self.topic_toggle)
        self.contents_button = QToolButton()
        self.contents_button.setObjectName('libraryOutline')
        self.contents_button.setText('En este artículo')
        self.contents_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.contents_menu = QMenu(self.contents_button)
        self.contents_button.setMenu(self.contents_menu)
        action_row.flow.addWidget(self.contents_button)
        self.open_button = QPushButton('Abrir herramienta')
        self.open_button.clicked.connect(self.open_selected)
        action_row.flow.addWidget(self.open_button)
        self.export_button = QToolButton()
        self.export_button.setObjectName('libraryOutline')
        self.export_button.setText('Exportar artículo')
        self.export_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        export_menu = QMenu(self.export_button)
        export_menu.addAction('Copiar texto', lambda: QApplication.clipboard().setText(self.text.toPlainText()))
        export_menu.addAction('Guardar con formato…', lambda: self.text.export_document(True))
        export_menu.addAction('Guardar como texto…', lambda: self.text.export_document(False))
        self.export_button.setMenu(export_menu)
        action_row.flow.addWidget(self.export_button)

        self.split = QSplitter(Qt.Orientation.Horizontal)
        self.split.setObjectName('librarySplit')
        self.split.setChildrenCollapsible(False)
        self.split.setHandleWidth(9)
        root.addWidget(self.split, 1)
        self.index_panel = QWidget()
        self.index_panel.setObjectName('libraryIndex')
        left = QVBoxLayout(self.index_panel)
        left.setContentsMargins(12, 12, 12, 12)
        self.split.addWidget(self.index_panel)
        self.search = QLineEdit()
        self.search.setObjectName('librarySearch')
        self.search.setPlaceholderText('Buscar en la biblioteca…')
        self.search.setAccessibleName('Buscar en la biblioteca')
        self.search.setClearButtonEnabled(True)
        left.addWidget(self.search)
        self.kind = QComboBox()
        self.kind.addItems(['Todo', 'Conceptos', 'Guías de herramientas', 'Referencia de fórmulas', 'Ejemplos resueltos'])
        self.kind.setAccessibleName('Tipo de artículo')
        left.addWidget(self.kind)
        self.match_status = QLabel()
        self.match_status.setObjectName('hint')
        left.addWidget(self.match_status)
        self.items = QTreeWidget()
        self.items.setObjectName('libraryTopics')
        self.items.setHeaderHidden(True)
        self.items.setIndentation(15)
        self.items.setAccessibleName('Temas y artículos de la biblioteca')
        left.addWidget(self.items, 1)

        self.article_panel = QWidget()
        self.article_panel.setObjectName('libraryArticle')
        right = QVBoxLayout(self.article_panel)
        right.setContentsMargins(10, 10, 10, 10)
        self.split.addWidget(self.article_panel)
        self.split.setStretchFactor(1, 1)
        self.text = ResponsiveHelpView()
        self.text.setMinimumHeight(130)
        self.text.anchorClicked.connect(self.follow_reference)
        self.guide_navigation = WrappingRow()
        self.guide_buttons = {}
        for key, label in (('fields', 'Campos'), ('diagrams', 'Esquemas'), ('results', 'Leer la salida')):
            button = QPushButton(label)
            button.setObjectName('guideChapter')
            button.clicked.connect(lambda checked=False, chapter=key: self.open_chapter(chapter))
            self.guide_navigation.flow.addWidget(button)
            self.guide_buttons[key] = button
        right.addWidget(self.guide_navigation)
        right.addWidget(self.text, 1)
        self.search.textChanged.connect(self.filter)
        self.search.returnPressed.connect(self.read_article)
        self.kind.currentIndexChanged.connect(lambda *_: self.filter(self.search.text()))
        self.items.currentItemChanged.connect(self.select_topic)
        self.items.itemClicked.connect(self.activate_topic)
        self.items.itemActivated.connect(self.activate_topic)
        self.filter('')
        self.adapt_layout()

    @staticmethod
    def search_entry(section):
        title = normalize(section['title'])
        aliases = tuple(normalize(alias) for alias in section.get('search_aliases', []))
        keywords = normalize(' '.join((section.get('original_title', ''), section['topic'], section['category'], *aliases)))
        body = [name + ' ' + value for name, value in section['blocks']]
        body.extend(form['syntax'] for form in section.get('forms', []))
        return section, title, aliases, keywords, normalize(' '.join(body))

    def select_topic(self, item, *_):
        if item is not None:
            row = item.data(0, Qt.ItemDataRole.UserRole)
            if row is not None:
                self.show_section(row)

    def activate_topic(self, item, *_):
        if item.data(0, Qt.ItemDataRole.UserRole) is not None:
            self.read_article()

    def read_article(self):
        if self.selected_index() is not None and self.compact:
            self.topic_toggle.setChecked(False)
            self.text.setFocus()

    def toggle_catalog(self, catalog):
        self.adapt_layout()
        if catalog:
            self.search.setFocus()

    def select_index(self, index):
        node = self.nodes.get(index)
        if node is not None:
            if node.parent() is not None:
                node.parent().setExpanded(True)
            self.items.setCurrentItem(node)
            self.items.scrollToItem(node)

    def selected_index(self):
        node=self.items.currentItem()
        return node.data(0,Qt.ItemDataRole.UserRole) if node is not None else None
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,'topic_toggle'):self.adapt_layout()
    def adapt_layout(self):
        compact = self.width() < 770
        was_compact = self.compact
        if compact and was_compact is False:
            self.split_sizes = self.split.sizes()
        self.compact = compact
        catalog = compact and self.topic_toggle.isChecked()
        self.topic_toggle.setVisible(compact)
        self.topic_toggle.setText('Leer artículo' if catalog else 'Catálogo')
        self.index_panel.setVisible(not compact or catalog)
        self.article_panel.setVisible(not catalog)
        if not compact and was_compact is not False:
            self.split.setSizes(self.split_sizes)
        self.refresh_actions()

    def refresh_actions(self):
        reading = not (self.compact and self.topic_toggle.isChecked())
        self.contents_button.setVisible(reading and bool(self.contents_menu.actions()))
        self.guide_navigation.setVisible(reading and bool(self.guide_anchors))
        for key, button in self.guide_buttons.items():
            button.setVisible(key in self.guide_anchors)
        self.export_button.setVisible(reading and bool(self.filtered))
        self.return_button.setVisible(self.on_open is not None and self.return_route is not None)
        example = getattr(self, 'selected_example', None)
        self.open_button.setText('Cargar datos del ejemplo' if example else 'Abrir herramienta')
        self.open_button.setVisible(reading and self.on_open is not None and self.selected_route is not None
                                    and (example is not None or self.selected_route != self.return_route))

    def filter(self, query):
        query = ' '.join(normalize(query).split())
        words = query.split()
        kind = KINDS[self.kind.currentIndex()]
        previous = getattr(self, 'selected_article_id', None) if query == self.last_query or not query else None
        self.last_query = query
        matches = []
        for section, title, aliases, keywords, body in self.search_index:
            if kind and section['content_kind'] != kind:
                continue
            if all(word in title or word in keywords or word in body for word in words):
                score = (title == query, query in aliases, title.startswith(query), all(word in title for word in words),
                         sum(word in title for word in words), sum(word in keywords for word in words))
                matches.append((score, section))
        if query:
            matches.sort(key=lambda match: match[0], reverse=True)
        self.filtered = [section for _, section in matches]
        self.match_status.setText(f'Coincidencias: {len(matches)}' if query else f'Artículos: {len(matches)}')
        self.items.blockSignals(True)
        self.items.clear()
        self.nodes = {}
        if query:
            for index, section in enumerate(self.filtered):
                self.items.addTopLevelItem(self.topic_node(section, index))
        else:
            for topic in TOPICS:
                entries = [(index, section) for index, section in enumerate(self.filtered) if section['topic'] == topic]
                if not entries:
                    continue
                group = QTreeWidgetItem([topic]);group.setFlags(Qt.ItemFlag.ItemIsEnabled)
                font = group.font(0);font.setBold(True);group.setFont(0, font)
                self.items.addTopLevelItem(group)
                for index, section in entries:
                    group.addChild(self.topic_node(section, index))
        self.items.blockSignals(False)
        if self.filtered:
            self.select_index(next((i for i, section in enumerate(self.filtered) if section['article_id'] == previous), 0))
        else:
            self.selected_route = None
            self.contents_menu.clear()
            self.guide_anchors.clear()
            self.text.setPlainText('No hay coincidencias. Probá otra palabra o cambiá el tipo de artículo.')
            self.refresh_actions()

    def topic_node(self, section, index):
        node = QTreeWidgetItem([section['title']])
        node.setData(0, Qt.ItemDataRole.UserRole, index)
        node.setToolTip(0, section['title'] + '\n' + KIND_LABELS[section['content_kind']] + ' · ' + section['purpose'])
        self.nodes[index] = node
        return node

    def select_functions(self):
        from .expression_editor import FORMULA_HELP
        self.select_article(FORMULA_HELP, kind=3)
    def select_article(self, identifier, kind=0):
        self.kind.setCurrentIndex(kind);self.search.clear()
        for index,section in enumerate(self.filtered):
            if section['article_id']==identifier:
                if self.selected_index() == index:
                    self.show_section(index)
                else:
                    self.select_index(index)
                self.topic_toggle.setChecked(False)
                return

    def set_return_route(self, route):
        had_context = self.guide_context is not None
        self.guide_context = None
        self.return_route = tuple(route) if route else None
        self.return_button.setToolTip(route[0] if route else '')
        if had_context and route is None:
            self.show_section(self.selected_index())
        self.refresh_actions()

    def select_tool(self,item, *, context=None, focused_field=''):
        from .tool_catalog import normalized_key
        self.topic_toggle.setChecked(False)
        self.set_return_route(item)
        self.guide_context = context
        key = normalized_key(item)
        section = next((section for section in self.sections
                        if section['route'] and section['route'][1:3] == key and section['content_kind'] == 'tool'), None)
        if section is not None:
            self.select_article(section['article_id'])
            if focused_field:
                names = ('course_tools','fir'), ('course_tools','iir'), ('course_tools','analog')
                chapter = 'diagrams' if key in names and focused_field[:1].isdigit() else 'fields'
                QTimer.singleShot(0, self, lambda: self.open_chapter(chapter))

    def open_chapter(self, key):
        anchor = self.guide_anchors.get(key)
        if anchor:
            self.text.scrollToAnchor(anchor)

    def show_section(self,row):
        if row is None or not 0<=row<len(self.filtered):return
        section = self.filtered[row]
        self.selected_article_id = section['article_id']
        self.selected_example = section.get('example')
        self.selected_route = section['route']
        blocks=list(section['blocks'])
        self.text._formula_number=0
        body = [f'<p>{html.escape(KIND_LABELS[section["content_kind"]] + " · " + section["topic"])}</p>',
                '<h1>'+html.escape(section['title'])+'</h1>']
        context = self.guide_context if self.selected_route == self.return_route else None
        if context is not None:
            body.append('<p style="color:#8ab6df"><b>'+html.escape(context.label)+'</b></p>')
            body.append('<p>'+html.escape(context.instructions)+'</p>')
        self.contents_menu.clear()
        self.guide_anchors.clear()
        heading_count = 0

        def add_heading(title, chapter=None):
            nonlocal heading_count
            destination = f'article-section-{heading_count}'
            heading_count += 1
            body.append(f'<h2><a name="{destination}"></a>{html.escape(title)}</h2>')
            self.contents_menu.addAction(title, lambda checked=False, anchor=destination: self.text.scrollToAnchor(anchor))
            if chapter:
                self.guide_anchors[chapter] = destination

        illustrations=diagrams_for(section)
        if context is not None and context.diagram:
            illustrations = sorted(illustrations, key=lambda diagram: diagram[0] != context.diagram)
        is_guide = section.get('field_reference', False)
        forms = section.get('forms',[])
        self.function_examples = []
        form_blocks = []
        def append_forms():
            for form in forms:
                title, syntax = form['title'], form['syntax']
                add_heading(title)
                body.append(f'<p><code>{html.escape(syntax)}</code></p>')
                lines = [syntax]
                for name, meaning in form['arguments']:
                    body.append(f'<p><b><code>{html.escape(name)}</code></b> · {html.escape(meaning)}</p>')
                    lines.append(f'{name} · {meaning}')
                for source, result in form['examples']:
                    index = len(self.function_examples)
                    self.function_examples.append(source)
                    body.append(f'<p><code>{html.escape(source)}</code> '
                                f'<a href="library:copy-formula/{index}">Copiar fórmula</a><br>{html.escape(result)}</p>')
                    lines.append(f'{source}\n{result}')
                form_blocks.append((title,'\n\n'.join(lines)))
        def append_illustrations():
            for index,(title,picture,caption) in enumerate(illustrations):
                url=QUrl(f'help-diagram-{index}');self.text.document().addResource(QTextDocument.ResourceType.ImageResource,url,picture)
                width=min(680,max(120,self.text.viewport().width()-50));height=round(picture.height()*width/picture.width())
                add_heading(title, 'diagrams' if is_guide and index == 0 else None)
                body.append(f'<img src="{url.toString()}" width="{width}" height="{height}"><p>'+html.escape(caption)+'</p>')

        def append_fields():
            from .library_fields import field_rows
            fields = field_rows(self.selected_route)
            if not fields:
                return
            add_heading('Campos de entrada', 'fields')
            for name, meaning in fields:
                body.append(f'<h3>{html.escape(name)}</h3><p>{html.escape(meaning)}</p>')
            form_blocks.append(('Campos de entrada','\n\n'.join(name+'\n'+meaning for name,meaning in fields)))

        for index,(title,content) in enumerate(blocks):
            add_heading(title, 'results' if is_guide and title == 'Cómo interpretar la salida' else None)
            if title=='Relación matemática':
                for line in content.splitlines():body.append(self.text._render_formula(line) or '<p>'+html.escape(line)+'</p>')
            else:
                for paragraph in content.split('\n\n'):body.append('<p style="line-height:150%">'+html.escape(paragraph).replace('\n','<br>')+'</p>')
            if index==0:
                append_forms()
                append_illustrations()
            if index==1 and is_guide:
                append_fields()
        insert_at = 2 if is_guide else 1
        blocks[insert_at:insert_at] = form_blocks
        if section.get('related'):
            add_heading('Temas relacionados')
            blocks.append(('Temas relacionados','\n'.join(title for _,title in section['related'])))
            for identifier,title in section['related']:body.append('<p><a href="library:article/'+identifier+'">'+html.escape(title)+'</a></p>')
        if section.get('examples'):
            add_heading('Ejemplos resueltos')
            blocks.append(('Ejemplos resueltos','\n'.join(title for _,title in section['examples'])))
            for example_id,title in section['examples']:body.append('<p><a href="library:example/'+example_id+'">'+html.escape(title)+'</a></p>')
        if section.get('route') is not None or section.get('reference'):
            body.append('<p><a href="library:glossary">Consultar el glosario de siglas y términos</a></p>')
        exported = [section['title']]
        if context is not None:
            exported.append(context.label+'\n'+context.instructions)
        exported.extend(title+'\n'+text for title,text in blocks)
        exported.extend(title+'\n'+caption for title,_,caption in illustrations)
        self.text._raw='\n\n'.join(exported)
        self.text.setHtml('<html><body style="font-family:Segoe UI;color:#dce4ef;font-size:11pt;margin:20px">'+''.join(body)+'</body></html>')
        self.refresh_actions()
    def follow_reference(self,url):
        if url.scheme()!='library':return
        if url.path().startswith('copy-formula/'):
            index = url.path().split('/',1)[1]
            if index.isascii() and index.isdigit() and int(index) < len(self.function_examples):
                QApplication.clipboard().setText(self.function_examples[int(index)])
                QToolTip.showText(QCursor.pos(),'Fórmula copiada',self.text)
            return
        if url.path().startswith('article/'):
            self.select_article(url.path().split('/',1)[1]);return
        if url.path().startswith('example/'):
            self.select_article('example:'+url.path().split('/',1)[1]);return
        if url.path()=='fields':
            self.open_chapter('fields')
        elif url.path()=='glossary':
            self.kind.setCurrentIndex(1);self.search.setText('Glosario');self.filter('Glosario')
    def open_selected(self):
        example=getattr(self,'selected_example',None)
        if example is not None and self.on_example:self.on_example(example)
        elif self.on_open and self.selected_route:self.on_open(self.selected_route)
    def return_to_tool(self):
        if self.on_open and self.return_route:self.on_open(self.return_route)
