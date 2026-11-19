"""Rounded area cards and direct actions, preserving the existing catalogue."""
from PySide6.QtCore import Qt,QSize
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,QFrame,QScrollArea,QSizePolicy,QLineEdit
from .tool_catalog import AREAS,AREA_BY_ID,ENTRIES,BY_KEY
from .theme_tokens import COLORS as C,AREA_COLORS
from .design import icon
from .wallpaper import BackgroundSurface

class ToolLink(QPushButton):
    def __init__(self,title,description,callback):
        super().__init__();self.setObjectName('toolLink');self.setAccessibleName(title);self.setCursor(Qt.CursorShape.PointingHandCursor);self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Minimum)
        row=QHBoxLayout(self);row.setContentsMargins(11,9,11,9);row.setSpacing(8);box=QVBoxLayout();box.setSpacing(3);row.addLayout(box,1)
        for text,name in [(title,'linkTitle'),(description,'muted')]:
            label=QLabel(text);label.setObjectName(name);label.setWordWrap(True);label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents);box.addWidget(label)
        arrow=QLabel('›');arrow.setObjectName('linkArrow');arrow.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents);row.addWidget(arrow)
        self.clicked.connect(callback)
    def sizeHint(self):return self.layout().sizeHint().expandedTo(QSize(100,54))

class ToolBrowser(QScrollArea):
    def __init__(self,window,area=None):
        super().__init__();self.window=window;self.area=area;self.cards=[];self.columns=None;self.quick_grid=None;self.quick_buttons=[];self.quick_columns=None;self.badges=[];self.link_groups=[]
        self.setWidgetResizable(True);self.setFrameShape(QFrame.Shape.NoFrame);self.content=BackgroundSurface();self.content.setObjectName('workspaceWallpaper');self.setWidget(self.content)
        root=QVBoxLayout(self.content);root.setContentsMargins(18,16,18,16);root.setSpacing(14)
        if area:
            label=QLabel(AREA_BY_ID[area][2]);label.setObjectName('muted');label.setWordWrap(True);root.addWidget(label)
        else:
            from .studio_cards import StudioHero,QuickAction
            hero=StudioHero();hero_box=QVBoxLayout(hero);hero_box.setContentsMargins(26,24,26,24);hero_box.setSpacing(12)
            title=QLabel('Señales y sistemas');title.setObjectName('welcomeTitle');title.setWordWrap(True);hero_box.addWidget(title)
            subtitle=QLabel('Análisis de señales, diseño de filtros y cálculo simbólico.');subtitle.setObjectName('muted');subtitle.setWordWrap(True);hero_box.addWidget(subtitle)
            self.home_search=QLineEdit();self.home_search.setObjectName('homeSearch');self.home_search.setPlaceholderText('Buscá una tarea: convolución, filtro FIR, transformada Z…');self.home_search.setClearButtonEnabled(True);self.home_search.addAction(icon('search'),QLineEdit.ActionPosition.LeadingPosition);hero_box.addWidget(self.home_search)
            self.quick_grid=QGridLayout();self.quick_grid.setSpacing(9);hero_box.addLayout(self.quick_grid)
            descriptions={'signal':'Fórmulas, muestras y ventanas','system':'Tiempo, frecuencia y polos','filter':'FIR, IIR y respuestas ideales'}
            for text,key,symbol,role,color in [('Crear señal',('basic','generate'),'signal','signal','green'),('Analizar sistema',('system_analysis',0),'response','system','blue'),('Diseñar filtro',('course_tools','fir'),'design','filter','purple')]:
                button=QuickAction(text,descriptions[role],symbol,color,lambda checked=False,k=key:window.open_workflow(BY_KEY[k]));button.setProperty('themeSymbol',symbol);button.setProperty('themeRole',color);self.quick_buttons.append(button)
            root.addWidget(hero)
        self.grid=QGridLayout();self.grid.setSpacing(14);root.addLayout(self.grid);self.search_empty=QLabel('No encontré una herramienta con ese nombre. Probá con una tarea, como Fourier, energía o polos.');self.search_empty.setObjectName('muted');self.search_empty.setWordWrap(True);self.search_empty.hide();root.addWidget(self.search_empty);root.addStretch()
        if area:
            sections=list(dict.fromkeys(entry['section'] for entry in ENTRIES if entry['area']==area))
            for section in sections:self.cards.append(self.make_card(area,section,[e for e in ENTRIES if e['area']==area and e['section']==section]))
        else:
            for key,title,description,symbol in AREAS:self.cards.append(self.make_card(key,title,[e for e in ENTRIES if e['area']==key]))
            self.home_search.textChanged.connect(self.apply_query);self.home_search.returnPressed.connect(self.open_search_match);self.apply_query('')
        self.reflow()
    def make_card(self,area,title,entries):
        color=AREA_COLORS[area];frame=QFrame();frame.setObjectName('browserSection');frame.setStyleSheet('QFrame#browserSection {border-top:2px solid '+color+';}')
        box=QVBoxLayout(frame);box.setContentsMargins(12,12,12,12);box.setSpacing(4);head=QHBoxLayout();head.setSpacing(9)
        tint=QColor(color);badge=QLabel();badge.setFixedSize(34,34);badge.setPixmap(icon(AREA_BY_ID[area][3],color).pixmap(22,22));badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet('background:rgba('+str(tint.red())+','+str(tint.green())+','+str(tint.blue())+',22);border-radius:10px;');head.addWidget(badge)
        self.badges.append((frame,badge,area))
        label=QLabel(title);label.setObjectName('sectionTitle');label.setWordWrap(True);head.addWidget(label,1)
        count=QLabel(str(len(entries)));count.setObjectName('badgeCount');count.setToolTip(str(len(entries))+' herramientas');head.addWidget(count);box.addLayout(head)
        links=[]
        for entry in entries:
            link=ToolLink(entry['title'],entry['summary'],lambda checked=False,value=entry:self.window.open_workflow(value));box.addWidget(link);links.append((entry,link))
        more=None
        if self.area is None:
            more=QPushButton('Ver todas las herramientas  ›');more.setObjectName('areaMore');more.clicked.connect(lambda checked=False,key=area:self.window.show_area(key));box.addWidget(more)
        self.link_groups.append((frame,links,more))
        box.addStretch();return frame
    def apply_query(self,text):
        from .tool_catalog import matches
        query=text.strip();found=False
        for frame,links,more in self.link_groups:
            visible=0
            for index,(entry,link) in enumerate(links):
                show=matches(entry,query) if query else index<2;link.setVisible(show);visible+=bool(show)
            frame.setVisible(visible>0)
            found=found or visible>0
            if more is not None:more.setVisible(not query and len(links)>2)
        self.search_empty.setVisible(bool(query) and not found)
        self.reflow()
    def open_search_match(self):
        from .tool_catalog import matches
        query=self.home_search.text().strip()
        if not query:return
        entry=next((entry for entry in ENTRIES if matches(entry,query)),None)
        if entry is not None:self.window.open_workflow(entry,query)
    def refresh_theme(self):
        for frame,badge,area in self.badges:
            color=AREA_COLORS[area];tint=QColor(color);frame.setStyleSheet('QFrame#browserSection {border-top:2px solid '+color+';}')
            badge.setPixmap(icon(AREA_BY_ID[area][3],color).pixmap(22,22));badge.setStyleSheet('background:rgba('+str(tint.red())+','+str(tint.green())+','+str(tint.blue())+',22);border-radius:10px;')
        for button in self.quick_buttons:
            if hasattr(button,'refresh_theme'):button.refresh_theme()
            else:button.setIcon(icon(button.property('themeSymbol'),C[button.property('themeRole')]))
        self.content.update()
    def resizeEvent(self,event):super().resizeEvent(event);self.reflow()
    def reflow(self):
        width=self.viewport().width();columns=2 if width>=760 else 1
        if self.quick_grid is not None:
            quick_columns=3 if width>=760 else 2 if width>=520 else 1
            if quick_columns!=self.quick_columns:
                self.quick_columns=quick_columns
                for index,button in enumerate(self.quick_buttons):self.quick_grid.addWidget(button,index//quick_columns,index%quick_columns)
                for index in range(3):self.quick_grid.setColumnStretch(index,1 if index<quick_columns else 0)
        if columns==self.columns:return
        self.columns=columns
        for index,card in enumerate(self.cards):self.grid.addWidget(card,index//columns,index%columns)
        self.grid.setColumnStretch(0,1);self.grid.setColumnStretch(1,1 if columns>1 else 0)
