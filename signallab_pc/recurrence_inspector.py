"""Inspect a computed recurrence without evaluating the input again."""
import math
import numpy as np
from .scalar_expression import integer_value


def inspect_step(result, index):
    trace=result.get('recurrence_trace')
    samples=result.get('numeric_samples')
    if trace is None or samples is None:
        raise ValueError('El inspector requiere las muestras numéricas del cálculo. La fórmula permanece disponible en Solución.')
    index=integer_value(index);start=int(result['origin']);offset=index-start
    if not 0<=offset<len(samples):
        raise ValueError(f'Elegí un índice entre {start} y {start+len(samples)-1}.')
    pair=lambda value:complex(*value)
    coefficients=[pair(value) for value in trace['coefficients']]
    history=[pair(value) for value in trace['history']]
    forcing=pair(trace['forcing_over_a0'][offset]);contributions=[]
    for k,coefficient in enumerate(coefficients[1:],1):
        previous=offset-k
        value=pair(samples[previous]) if previous>=0 else history[-previous-1]
        contribution=-coefficient*value
        contributions.append(dict(lag=k,index=index-k,value=value,coefficient=coefficient,
                                  contribution=contribution,source='Calculada' if previous>=0 else 'Condición inicial'))
    parts=[forcing]+[row['contribution'] for row in contributions]
    if not np.isfinite(parts).all():
        raise ValueError('Un aporte de este paso excede el rango numérico. Las muestras y la fórmula del cálculo se conservan.')
    try:reconstructed=complex(math.fsum(v.real for v in parts),math.fsum(v.imag for v in parts))
    except OverflowError as exc:raise ValueError('La suma de aportes excede el rango numérico del inspector.') from exc
    computed=pair(samples[offset])
    return dict(index=index,forcing=forcing,contributions=contributions,computed=computed,
                reconstructed=reconstructed,residual=computed-reconstructed,normalization=trace['normalization'])


def step_summary(result, index):
    from .result_summary import Summary,Section,number
    data=inspect_step(result,index);n=data['index']
    rows=[('f['+str(n)+']/a₀',number(data['forcing']))]
    for term in data['contributions']:
        rows.append((f"−(a{term['lag']}/a₀) · y[{term['index']}]",
                     f"−({number(term['coefficient'])}) · ({number(term['value'])}) = {number(term['contribution'])} · {term['source']}"))
    return Summary('Recurrencia · paso n='+str(n),[
        Section('Datos del último cálculo',rows=[('Índice inicial n₀',str(result['origin'])),('a₀',data['normalization'])],
                paragraphs=['Se despeja y[n] = f[n]/a₀ − Σ(aₖ/a₀)·y[n−k]. Los aportes se calculan con los datos normalizados y las muestras guardadas, sin volver a evaluar f[n].']),
        Section('Aporte de cada término',rows=rows),
        Section('Salida',rows=[('Suma de aportes',number(data['reconstructed'])),('y['+str(n)+'] calculada',number(data['computed'])),
                              ('Diferencia numérica',number(data['residual']))],
                paragraphs=['La diferencia mide redondeo y coherencia de este paso numérico; no es una prueba de la fórmula simbólica. Al editar los datos del formulario, el inspector conserva el último cálculo hasta recalcular.'])])


from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLineEdit,QLabel,QPushButton
from .report_view import ReportView,report_panel


class RecurrenceInspector(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent);self.result=None
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);bar=QHBoxLayout();layout.addLayout(bar)
        self.previous=QPushButton('← Anterior');self.next=QPushButton('Siguiente →')
        self.index=QLineEdit();self.index.setAccessibleName('Índice n a inspeccionar');self.index.setMaximumWidth(180)
        self.range=QLabel();self.range.setWordWrap(True)
        bar.addWidget(self.previous);bar.addWidget(QLabel('n ='));bar.addWidget(self.index);bar.addWidget(self.next);bar.addWidget(self.range,1)
        self.report=ReportView();layout.addWidget(report_panel(self.report),1)
        self.previous.clicked.connect(lambda:self.move(-1));self.next.clicked.connect(lambda:self.move(1));self.index.returnPressed.connect(self.show_step)

    def set_result(self,result):
        self.result=result
        if not result.get('recurrence_trace') or result.get('numeric_samples') is None:
            self.previous.setEnabled(False);self.next.setEnabled(False);self.index.setEnabled(False)
            self.report.setPlainText('Calculá una ecuación con muestras numéricas para inspeccionar sus pasos.');return
        start=int(result['origin']);end=start+len(result['numeric_samples'])-1
        self.index.setEnabled(True);self.index.setText(str(start));self.range.setText(f'Intervalo calculado: {start} a {end}');self.show_step()

    def move(self,delta):
        if self.result is None:return
        from .numeric_input import integer_field
        try:self.index.setText(str(integer_field(self.index)+delta));self.show_step()
        except ValueError as exc:self.report.setPlainText(str(exc))

    def show_step(self):
        if self.result is None:return
        from .numeric_input import integer_field
        try:
            index=integer_field(self.index);self.report.set_readable(step_summary(self.result,index))
            start=int(self.result['origin']);self.previous.setEnabled(index>start);self.next.setEnabled(index<start+len(self.result['numeric_samples'])-1)
        except ValueError as exc:self.report.setPlainText(str(exc))
