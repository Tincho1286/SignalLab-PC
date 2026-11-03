"""Preview custom appearance locally; apply only when the dialog is accepted."""
from pathlib import Path
from PySide6.QtCore import Qt,QRectF
from PySide6.QtGui import QPainter,QColor
from PySide6.QtWidgets import QDialog,QVBoxLayout,QFormLayout,QHBoxLayout,QWidget,QComboBox,QPushButton,QLabel,QSlider,QColorDialog,QFileDialog,QDialogButtonBox,QMessageBox,QScrollArea
from . import theme_presets
from .custom_appearance import validate,palette,save
from . import wallpaper


class Preview(QWidget):
    def __init__(self):super().__init__();self.config={};self.setMinimumHeight(180)
    def paintEvent(self,event):
        colors=palette(self.config);painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        wallpaper.paint(painter,QRectF(self.rect()),colors,self.config)
        box=QRectF(16,18,max(10,self.width()*.68),min(142,max(10,self.height()-36)));painter.setPen(QColor(colors['border']));painter.setBrush(wallpaper.panel_color(colors['panel'],self.config.get('surface_opacity',100)));painter.drawRoundedRect(box,10,10)
        painter.setPen(QColor(colors['text']));painter.drawText(box.adjusted(16,12,-16,-12),Qt.AlignmentFlag.AlignTop,'SignalLab · Vista previa')
        painter.setPen(QColor(colors['muted']));painter.drawText(box.adjusted(16,42,-16,-12),Qt.AlignmentFlag.AlignTop,'Vista previa del fondo de los menús')
        button=QRectF(box.x()+16,box.bottom()-48,120,30);painter.setPen(QColor(colors['primary']));painter.setBrush(QColor(colors['primary']));painter.drawRoundedRect(button,7,7);painter.setPen(QColor(colors['on_primary']));painter.drawText(button,Qt.AlignmentFlag.AlignCenter,'Calcular')
        painter.end()


class CustomThemeDialog(QDialog):
    def __init__(self,window):
        super().__init__(window);self._owner=window;self.config=dict(theme_presets.CUSTOM);self.setWindowTitle('Tema personalizado');available=self.screen().availableGeometry();self.resize(min(660,available.width()-40),min(660,available.height()-60))
        root=QVBoxLayout(self);scroll=QScrollArea();scroll.setWidgetResizable(True);body=QWidget();content=QVBoxLayout(body);form=QFormLayout();content.addLayout(form);scroll.setWidget(body);root.addWidget(scroll,1)
        self.base=QComboBox()
        for key,(name,_) in theme_presets.PRESETS.items():
            if key!='custom':self.base.addItem(name,key)
        self.base.setCurrentIndex(max(0,self.base.findData(self.config['base'])));form.addRow('Colores de base',self.base)
        self.surface_mode=QComboBox();self.surface_mode.addItems(['Opaco','Translúcido','Transparente']);form.addRow('Fondo de menús',self.surface_mode)
        self.surface_opacity=QSlider(Qt.Orientation.Horizontal);self.surface_opacity.setRange(0,100);self.surface_opacity.setValue(self.config.get('surface_opacity',100));self.surface_percent=QLabel();row=QHBoxLayout();row.addWidget(self.surface_opacity,1);row.addWidget(self.surface_percent);form.addRow('Opacidad del fondo',row)
        self.surface_opacity.setToolTip('0 %: transparente · 100 %: opaco. Se aplica a los fondos de navegación y paneles, sin desvanecer textos ni controles.')
        self.accent=QPushButton('Elegir color…');self.accent.clicked.connect(self.choose_accent);form.addRow('Acento',self.accent)
        row=QHBoxLayout();self.photo_label=QLabel();self.photo_label.setWordWrap(True);row.addWidget(self.photo_label,1)
        choose=QPushButton('Elegir foto…');choose.clicked.connect(self.choose_photo);remove=QPushButton('Quitar');remove.clicked.connect(self.remove_photo);row.addWidget(choose);row.addWidget(remove);form.addRow('Foto de fondo',row)
        self.opacity=QSlider(Qt.Orientation.Horizontal);self.opacity.setRange(0,100);self.opacity.setValue(self.config['opacity']);self.percent=QLabel();row=QHBoxLayout();row.addWidget(self.opacity,1);row.addWidget(self.percent);form.addRow('Intensidad de la foto',row)
        self.fit=QComboBox();self.fit.addItem('Cubrir el área · recortar bordes','cover');self.fit.addItem('Mostrar la foto completa','contain');self.fit.setCurrentIndex(max(0,self.fit.findData(self.config['fit'])));form.addRow('Encuadre',self.fit)
        note=QLabel('La opacidad deja ver la foto detrás de los menús. Los campos de entrada, informes y figuras conservan su fondo de lectura. La foto se guarda sólo en este equipo.');note.setWordWrap(True);content.addWidget(note)
        self.preview=Preview();content.addWidget(self.preview,1)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Apply|QDialogButtonBox.StandardButton.Cancel);buttons.button(QDialogButtonBox.StandardButton.Apply).setText('Aplicar tema');buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Cancelar');buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept);buttons.rejected.connect(self.reject);root.addWidget(buttons)
        self.base.currentIndexChanged.connect(self.update_preview);self.opacity.valueChanged.connect(self.update_preview);self.fit.currentIndexChanged.connect(self.update_preview);self.surface_opacity.valueChanged.connect(self.update_preview);self.surface_mode.activated.connect(self.choose_surface_mode);self.update_preview()

    def update_preview(self,*_):
        self.config.update(base=self.base.currentData(),opacity=self.opacity.value(),fit=self.fit.currentData(),surface_opacity=self.surface_opacity.value());self.config=validate(self.config)
        value=self.config['surface_opacity'];self.surface_percent.setText(str(value)+' %');self.surface_mode.setCurrentIndex(0 if value==100 else 2 if value==0 else 1)
        self.photo_label.setText(Path(self.config['photo']).name if self.config['photo'] else 'Sin foto');self.photo_label.setToolTip(self.config['photo']);self.percent.setText(str(self.config['opacity'])+' %')
        colors=palette(self.config);self.accent.setStyleSheet('background:'+colors['primary']+';color:'+colors['on_primary']+';');self.preview.config=dict(self.config);self.preview.update()

    def choose_surface_mode(self,index):
        self.surface_opacity.setValue(100 if index==0 else 0 if index==2 else self.surface_opacity.value() if 0<self.surface_opacity.value()<100 else 70)
    def choose_accent(self):
        color=QColorDialog.getColor(QColor(palette(self.config)['accent']),self,'Color de acento')
        if color.isValid():self.config['accent']=color.name();self.update_preview()

    def choose_photo(self):
        path,_=QFileDialog.getOpenFileName(self,'Foto de fondo','','Imágenes (*.png *.jpg *.jpeg *.webp *.bmp)')
        if not path:return
        try:wallpaper.read_photo(path)
        except (ValueError,MemoryError,OSError) as exc:QMessageBox.warning(self,'No se pudo cargar la foto',str(exc));return
        self.config['photo']=path;self.update_preview()

    def remove_photo(self):self.config['photo']='';self.update_preview()

    def accept(self):
        from .appearance import apply
        previous=dict(theme_presets.CUSTOM);old_key=theme_presets.CURRENT
        try:
            config=validate(self.config);config['photo']=wallpaper.save_photo(config['photo']) if config['photo'] else ''
            theme_presets.set_custom(config);apply(self._owner,'custom',persist=False)
            save(config)
            from PySide6.QtCore import QSettings
            QSettings('SignalLab','Desktop071').setValue('appearance/theme','custom');theme_presets.HAS_CUSTOM=True
            wallpaper.clean_previous(config['photo'])
        except (ValueError,MemoryError,OSError) as exc:
            theme_presets.set_custom(previous);apply(self._owner,old_key,persist=False);QMessageBox.warning(self,'No se pudo aplicar el tema',str(exc));return
        super().accept()


def configure(window):
    dialog=CustomThemeDialog(window);dialog.exec()
    for key,action in getattr(window,'theme_actions',{}).items():action.setChecked(key==theme_presets.CURRENT)
    wallpaper._cache.clear();dialog.deleteLater()
