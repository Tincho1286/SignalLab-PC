"""One representation problem for numbers and digital filter coefficients."""
from pathlib import Path
import csv
from PySide6.QtCore import Qt,QAbstractTableModel
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QScrollArea,QComboBox,QLineEdit,QLabel,QPushButton,QFileDialog,QMessageBox,QTableView
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from .precision import Encoding,represent,quantize_coefficients,precision_summary
from .numeric_input import integer_field
from .coefficient_editor import CoefficientEditor,TransferPreview
from .transfer_input import install_formula_editor,remember_system,read_system
from .report_view import report_panel
from .transfer_report import TransferResultReport
from .active_stack import ActiveTabs
from .result_state import ResultState
from .system_result_actions import SystemResultActions
from .filter_arithmetic import simulate,simulation_summary


class CoefficientTable(QAbstractTableModel):
    columns=[('coefficient','Coeficiente'),('component','Componente'),('original','Original'),('stored','Representado'),('error','Error salida − entrada'),('classification','Clase'),('word','Palabra binaria')]
    def __init__(self,parent=None):super().__init__(parent);self.rows=[]
    def set_rows(self,rows):self.beginResetModel();self.rows=rows;self.endResetModel()
    def rowCount(self,parent=None):return len(self.rows)
    def columnCount(self,parent=None):return len(self.columns)
    def data(self,index,role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role not in (Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.ToolTipRole):return None
        value=self.rows[index.row()][self.columns[index.column()][0]]
        if isinstance(value,float):return format(value,'.17g')
        if isinstance(value,str) and len(value)>128 and role==Qt.ItemDataRole.DisplayRole:return value[:48]+'…'+value[-48:]+' (vista abreviada)'
        return str(value)
    def headerData(self,section,orientation,role=Qt.ItemDataRole.DisplayRole):
        if role!=Qt.ItemDataRole.DisplayRole:return None
        return self.columns[section][1] if orientation==Qt.Orientation.Horizontal else str(section+1)


class PrecisionPanel(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.result=None;self.result_id=None;self.parent_id=None
        root=QHBoxLayout(self);controls=QWidget();form=QFormLayout(controls);form.setProperty('stackFields',True);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.study=QComboBox();self.study.addItems(['Representar un número','Coeficientes de un filtro','Filtrar con precisión finita']);form.addRow('Estudio',self.study)
        self.format=QComboBox()
        for title,key in [('Punto fijo con signo · Q','fixed'),('IEEE 754 · binary16','float16'),('IEEE 754 · binary32','float32'),('IEEE 754 · binary64','float64')]:self.format.addItem(title,key)
        form.addRow('Formato de almacenamiento',self.format)
        self.integer_bits=QLineEdit('2');self.fractional_bits=QLineEdit('14');self.rounding=QComboBox();self.rounding.addItems(['Redondeo · empates alejando de cero','Truncamiento hacia cero'])
        form.addRow('Bits enteros, incluyendo signo',self.integer_bits);form.addRow('Bits fraccionarios',self.fractional_bits);form.addRow('Conversión en punto fijo',self.rounding)
        self.value=QLineEdit('0.7');form.addRow('Valor o expresión constante',self.value)
        self.system_box=QWidget();sf=QFormLayout(self.system_box);sf.setProperty('stackFields',True);sf.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.domain=QComboBox();self.domain.addItems(['Continuo','Discreto']);self.domain.setCurrentIndex(1);self.domain.hide()
        self.b=CoefficientEditor('1');self.a=CoefficientEditor('1, -0.9');self.b.set_domain(True);self.a.set_domain(True);self.preview=TransferPreview(self.b,self.a)
        sf.addRow(self.preview);sf.addRow('Numerador b',self.b);sf.addRow('Denominador a',self.a);install_formula_editor(self,sf)
        copy=QPushButton('Copiar un filtro anterior…');copy.clicked.connect(self.choose);sf.addRow(copy)
        from .system_import import install_system_import
        self.system_import=install_system_import(copy,window,self.set_system,self.choose,domains=['digital'],allow_advance=False)
        self.system_form=sf
        self.structure=QComboBox();self.structure.addItems(['Conservar secciones si existen','Polinomios directos']);sf.addRow('Representación de H(z)',self.structure)
        self.scope=QLabel('Se redondean los coeficientes almacenados. Los cálculos posteriores usan doble precisión; no se simulan redondeos de productos, sumas o estados. a[0]=1 es implícito y no se cuantiza.');self.scope.setWordWrap(True);sf.addRow(self.scope);form.addRow(self.system_box)
        from .toolbox import LocalInput,ResultView
        self.simulation_box=QWidget();af=QFormLayout(self.simulation_box);af.setProperty('stackFields',True);af.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.input=LocalInput('Entrada x[n]','discrete');self.input.bind_project(window);self.input.expression.setText('impulse(n)');af.addRow(self.input)
        self.operation_rounding=QComboBox();self.operation_rounding.addItems(['Productos, sumas, salida y memorias','Sólo salida y memorias']);af.addRow('Dónde redondear',self.operation_rounding)
        self.guard_bits=QLineEdit('4');af.addRow('Bits enteros extra en las sumas',self.guard_bits)
        self.overflow=QComboBox();self.overflow.addItems(['Saturación','Complemento a dos cíclico']);af.addRow('Desborde durante la ejecución',self.overflow)
        self.initial=QLineEdit('0');self.initial.setToolTip('Un valor inicial para todas las memorias o una lista d[0], d[1], … . En SOS: las dos memorias de la sección 1, las de la sección 2, etc. Se admiten pi, fracciones y complejos.');af.addRow('Memoria inicial · un valor o lista',self.initial)
        self.tail=QLineEdit('64');af.addRow('Ceros agregados al final',self.tail);form.addRow(self.simulation_box)
        self.calculate_button=QPushButton('Calcular precisión');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);form.insertRow(0,self.calculate_button)
        self.result_state=ResultState([self.study,self.format,self.integer_bits,self.fractional_bits,self.rounding,self.value,self.b,self.a,self.definition_mode,self.transfer_formula,self.structure,self.operation_rounding,self.guard_bits,self.overflow,self.initial,self.tail],self.calculate_button,[self.input]);form.insertRow(1,self.result_state)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);root.addWidget(scroll,1)
        right=QWidget();out=QVBoxLayout(right);root.addWidget(right,2);self.tabs=ActiveTabs();out.addWidget(self.tabs,1)
        self.report=TransferResultReport();self.tabs.addTab(report_panel(self.report),'Informe')
        plot=QWidget();pl=QVBoxLayout(plot);self.figure=Figure(figsize=(7,5));self.canvas=FigureCanvasQTAgg(self.figure);self.toolbar=NavigationToolbar2QT(self.canvas,self);pl.addWidget(self.toolbar);pl.addWidget(self.canvas,1);self.tabs.addTab(plot,'Comparación')
        self.table=QTableView();self.table_model=CoefficientTable(self.table);self.table.setModel(self.table_model);self.table.setAlternatingRowColors(True);self.tabs.addTab(self.table,'Coeficientes')
        self.output_view=ResultView(details=False);self.output_index=self.tabs.addTab(self.output_view,'Salida y');self.tabs.setTabVisible(self.output_index,False)
        self.actions=SystemResultActions(window);self.actions.reuse_excluded.add(('sampling',5));out.addWidget(self.actions);self.actions.hide()
        self.export=QPushButton('Exportar representación JSON…');self.export.clicked.connect(self.export_result);out.addWidget(self.export);self.export.setEnabled(False)
        for field in (self.b,self.a):field.textChanged.connect(self.update_structure)
        self.definition_mode.currentIndexChanged.connect(self.update_structure)
        self.study.currentIndexChanged.connect(self.update_fields);self.format.currentIndexChanged.connect(self.update_fields);self.operation_rounding.currentIndexChanged.connect(self.update_fields);self.update_fields()
        self.update_structure();self.tabs.setTabVisible(1,False);self.tabs.setTabVisible(2,False);self.report.setPlainText('Elegí un formato y completá el número o H(z). El resultado indicará qué valores se pueden almacenar y qué cambios produce la conversión.')
    def update_fields(self,*_):
        form=self.integer_bits.parentWidget().layout();fixed=self.format.currentData()=='fixed';system=self.study.currentIndex()!=0;simulation=self.study.currentIndex()==2
        for widget in (self.integer_bits,self.fractional_bits,self.rounding):form.setRowVisible(widget,fixed)
        form.setRowVisible(self.value,not system);self.system_box.setVisible(system)
        self.simulation_box.setVisible(simulation);self.simulation_box.layout().setRowVisible(self.guard_bits,fixed and self.operation_rounding.currentIndex()==0);self.simulation_box.layout().setRowVisible(self.overflow,fixed)
        self.scope.setText('Se simula la realización II transpuesta: productos, sumas y memorias según el modo elegido. La entrada y los coeficientes se cuantizan primero. La comparación separa el error de almacenamiento y el de ejecución.' if simulation else 'Se redondean los coeficientes almacenados. Los cálculos posteriores usan doble precisión; este estudio no redondea operaciones internas. a[0]=1 es implícito y no se cuantiza.')
    def update_structure(self,*_):
        source=getattr(self,'_preserved_system',None)
        has_sections=source is not None and source.sos is not None and self.definition_mode.currentIndex()==0 and (self.b.text(),self.a.text(),self.domain.currentIndex())==getattr(self,'_preserved_definition',None)
        self.system_form.setRowVisible(self.structure,has_sections)
    def set_system(self,system,key=None):
        if system.domain!='digital':raise ValueError('Esta herramienta requiere H(z).')
        from .systems_panel import list_text
        if self.study.currentIndex()!=2:self.study.setCurrentIndex(1)
        self.b.setText(list_text(system.b));self.a.setText(list_text(system.a));self.parent_id=key;remember_system(self,system);self.structure.setCurrentIndex(0);self.update_structure()
    def choose(self):
        key=self.window.choose_record('system',domains=['digital'])
        if key:self.set_system(self.window.project.get(key),key)
    def calculate(self):
        try:
            fixed=self.format.currentData()=='fixed';encoding=Encoding(self.format.currentData(),integer_field(self.integer_bits) if fixed else 2,integer_field(self.fractional_bits) if fixed else 14,'round' if self.rounding.currentIndex()==0 else 'truncate')
            study=self.study.currentIndex();snapshot=self.result_state.snapshot()
            if study:
                system=read_system(self);preserve=self.structure.currentIndex()==0;parent=self.parent_id
                if study==2:
                    from .systems_panel import parse_list
                    source=self.input.read();input_parent=self.input.reference_id;initial=parse_list(self.initial.text());tail=integer_field(self.tail);guard=integer_field(self.guard_bits) if fixed and self.operation_rounding.currentIndex()==0 else 0;overflow='saturate' if self.overflow.currentIndex()==0 or not fixed else 'wrap';operations=self.operation_rounding.currentIndex()==0
                    job=lambda:simulate(system,source,encoding,preserve_sections=preserve,initial=initial,tail=tail,guard_bits=guard,overflow=overflow,operations=operations)
                else:job=lambda:quantize_coefficients(system,encoding,preserve)
            else:
                source=self.value.text();parent=None;job=lambda:represent(source,encoding)
            def accept(result):
                simulation=result.get('simulation',False)
                self.result=result;self.report.set_readable(simulation_summary(result) if simulation else precision_summary(result));self.tabs.setCurrentIndex(0);self.tabs.setTabVisible(self.output_index,simulation)
                is_system='system' in result;self.tabs.setTabVisible(1,is_system);self.tabs.setTabVisible(2,is_system);self.actions.setVisible(is_system)
                if is_system:
                    original_key=self.window.publish(result['source'],operation='Entrada para precisión de coeficientes',parents=[parent] if parent else [])
                    self.result_id=self.window.publish(result['system'],operation='Cuantización de coeficientes',parents=[original_key]);self.actions.set_result(result['system'],self.result_id);self.table_model.set_rows(result['rows']);figure_window=getattr(self.canvas,'_signallab_window',None)
                    if figure_window is not None:figure_window.setWindowTitle('Precisión de coeficientes · SignalLab')
                    self.draw()
                    if simulation:
                        source_key=self.window.publish(result['source_signal'],operation='Entrada de precisión finita',parents=[input_parent] if input_parent else [])
                        self.window.publish(result['output'],operation='Ejecución con precisión finita',parents=[original_key,self.result_id,source_key]);self.output_view.show_result(result['output'])
                        if figure_window is not None:figure_window.setWindowTitle('Ejecución con precisión finita · SignalLab')
                    self.window.publish({'format':result['encoding'].name,'metrics':result['metrics'],'report':self.report.toPlainText()},title='Ejecución con precisión finita' if simulation else 'Precisión de coeficientes',operation='Comparación de ejecución' if simulation else 'Comparación de almacenamiento',parents=[original_key,self.result_id])
                else:self.result_id=self.window.publish(result,title='Representación '+result['format'],operation='Representación numérica');self.table_model.set_rows([])
                self.export.setText('Exportar comparación CSV…' if simulation else 'Exportar coeficientes CSV…' if is_system else 'Exportar representación JSON…');self.export.setEnabled(True);self.result_state.accept(snapshot)
            self.window._run_operation('Calculando efectos de precisión…',job,accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá el formato o la entrada',str(exc))
    def draw(self):
        import numpy as np
        from .theme_tokens import COLORS as C
        from .signal_plot import configure_axis,plot_samples
        if self.result.get('simulation'):
            self.draw_simulation();return
        data=self.result;self.figure.clear();axes=self.figure.subplots(3,1,sharex=True);w=data['omega']
        for system,h,label,color in [(data['source'],data['original_response'],'Original',C['muted']),(data['system'],data['stored_response'],'Coeficientes cuantizados',C['blue'])]:
            finite=np.isfinite(h);scale=max(1,float(np.max(abs(h.real[finite]),initial=0)),float(np.max(abs(h.imag[finite]),initial=0)));amplitude=abs(h/scale);valid=np.isfinite(h)&(amplitude>0)
            db=np.full(len(w),np.nan);db[valid]=20*np.log10(scale)+20*np.log10(amplitude[valid]);phase=np.full(len(w),np.nan);phase[valid]=np.angle(h[valid]);delay=system.group_delay(w)
            axes[0].plot(w,db,label=label,color=color);plot_samples(axes[1],w,phase,color=color,phase=True);axes[2].plot(w,delay,color=color)
        for axis,label in zip(axes,('Módulo (dB)','Fase principal (rad)','Retardo (muestras)')):axis.set_ylabel(label);axis.set_xlim(0,np.pi);axis.grid(alpha=.2)
        axes[0].legend();configure_axis(axes[2],units='rad/muestra',label='ω (rad/muestra)');self.figure.set_layout_engine('constrained');self.canvas.draw_idle()
    def draw_simulation(self):
        import numpy as np
        from .theme_tokens import COLORS as C
        from .signal_plot import configure_axis,plot_samples
        data=self.result;self.figure.clear();axes=self.figure.subplots(3,1,sharex=True);x=data['output'].axis
        for values,label,color in [(data['original_reference'],'Referencia original',C['muted']),(data['storage_reference'],'Sólo almacenamiento',C['green']),(data['output'].values,'Ejecución finita',C['blue'])]:
            plot_samples(axes[0],x,values.real,discrete=True,label=label,color=color);plot_samples(axes[1],x,values.imag,discrete=True,color=color)
        scale=data['arithmetic_metrics']['scale'];error=np.abs(data['output'].values/scale-data['storage_reference']/scale)
        plot_samples(axes[2],x,error,discrete=True,color=C['amber'])
        for axis,label in zip(axes,('Salida · parte real','Salida · parte imaginaria','|Error aritmético| / S')):
            axis.set_ylabel(label);configure_axis(axis,discrete_index=True,label='Índice n (muestras)');axis.grid(alpha=.2)
        axes[0].legend();self.figure.set_layout_engine('constrained');self.canvas.draw_idle()
    def export_result(self):
        if self.result is None:return
        system='system' in self.result
        path,_=QFileDialog.getSaveFileName(self,'Exportar último resultado','coeficientes.csv' if system else 'representacion.json','Tabla CSV (*.csv)' if system else 'Documento JSON (*.json)')
        if not path:return
        if not Path(path).suffix:path+='.csv' if system else '.json'
        try:
            from .atomic_file import atomic_text_file,write_json
            if system:
                if self.result.get('simulation'):
                    from .atomic_file import atomic_text_file
                    import numpy as np
                    with atomic_text_file(path,newline='') as stream:
                        writer=csv.writer(stream);writer.writerow(['n','entrada_q_real','entrada_q_imag','salida_real','salida_imag','referencia_original_real','referencia_original_imag','referencia_almacenada_real','referencia_almacenada_imag'])
                        for index,n in enumerate(self.result['output'].axis):
                            row=[int(n)]
                            for array in (self.result['input'],self.result['output'].values,self.result['original_reference'],self.result['storage_reference']):
                                value=array[index];row.extend((float(value.real),float(value.imag)) if np.isfinite(value) else ('',''))
                            writer.writerow(row)
                    return
                rows=self.result['rows']
                with atomic_text_file(path,newline='') as stream:
                    writer=csv.DictWriter(stream,fieldnames=list(rows[0]) if rows else ['coefficient']);writer.writeheader();writer.writerows(rows)
            else:write_json(path,self.result)
        except Exception as exc:QMessageBox.warning(self,'No se pudo exportar',str(exc))
