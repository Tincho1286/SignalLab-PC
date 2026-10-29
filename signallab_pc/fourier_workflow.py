"""Copy Fourier definitions without confusing time, frequency or finite support."""
import ast
import math
from .expression_dialects import to_numeric,to_symbolic
from .numeric_input import integer_field,real_field


def signature(page):
    panel=getattr(page,'panel',None)
    if panel is not None and panel.__class__.__name__=='SymbolicFourierPanel':
        return panel.discrete,panel.inverse,True,panel
    key=tuple(page.tool_item[1:3])
    options={('fourier',0):(True,False),('fourier',1):(False,False),('fourier',3):(False,True),
             ('inverse_dtft',0):(True,True),('basic','dft'):(True,False),('course_tools','fft'):(True,False)}
    if key not in options:return None
    source=getattr(getattr(page,'context',None),'source',None) or getattr(panel,'source',None) or getattr(page,'first',None)
    return (*options[key],False,source)


def _origin(field):
    origin=getattr(field,'_expression_origin',None)
    return origin[1] if origin and origin[0]==field.expression.text() else None


def _numeric_conditions(field):
    origin=getattr(field,'_expression_origin',None)
    conditions=getattr(field,'_expression_conditions',()) if origin and origin[0]==field.expression.text() else ()
    if not conditions and _origin(field) and field.project_window:
        expression=field.project_window.project.expression(_origin(field))
        if expression:conditions=expression.conditions
    return tuple(conditions)


def _support(panel):
    conditions=[]
    if panel.lower.text().strip() not in ('-oo','-infinity'):conditions.append('(n >= ('+panel.lower.text()+'))')
    if panel.upper.text().strip() not in ('oo','infinity'):conditions.append('(n <= ('+panel.upper.text()+'))')
    text=panel.expression.text()
    return 'Piecewise((('+text+'), '+' and '.join(conditions)+'), (0, True))' if conditions else text


def prepare_fourier_inputs(source,target):
    from .workflow_inputs import InputCopy
    a=signature(source);b=signature(target)
    if a is None or b is None:return None
    discrete,inverse,symbolic,field=a;other_discrete,other_inverse,other_symbolic,dst=b
    if discrete!=other_discrete:return InputCopy(note='Se conservó la entrada de este dominio. Una señal continua y una secuencia discreta requieren una operación de muestreo, no un cambio de método.')
    if inverse!=other_inverse:return InputCopy(note='Directa recibe la señal e Inversa recibe su espectro. Cada operación conserva su entrada; para usar una salida calculada, elegila desde Resultados.')
    if symbolic==other_symbolic:return None
    if not symbolic:
        if field is None or field.mode.currentIndex()!=0:
            return InputCopy(note='Este registro contiene valores finitos; no define una fórmula analítica única. Se conserva la entrada algebraica. Podés seguir trabajando con los datos en el método numérico.')
        if field.kind=='frequency' and field.frequency_units.currentText()!=('rad/muestra' if discrete else 'rad/s'):
            return InputCopy(note='Se conserva la entrada: rad/s y rad/muestra no se convierten automáticamente.')
        count=integer_field(field.count)
        if field.kind=='discrete':
            integer_field(field.origin)
            if count<1:raise ValueError('La cantidad de muestras debe ser positiva.')
        else:
            first=real_field(field.origin);step=real_field(field.step);last=first+(count-1)*step
            if count<2 or step<=0 or not math.isfinite(last) or last<=first:raise ValueError('El intervalo numérico requiere al menos dos puntos y un paso positivo que distinga sus extremos.')
        text=to_symbolic(field.expression.text());conditions=list(_numeric_conditions(field))
        if not discrete:
            start=field.origin.text();stop='('+start+')+('+field.count.text()+'-1)*('+field.step.text()+')';variable='w' if inverse else 't'
            from .continuous_expression import has_dirac,finite_definition
            if has_dirac(field.expression.text()):
                if inverse:return InputCopy(note='Esta entrada numérica requiere un espectro ordinario. Para impulsos ideales en frecuencia, definí X(ω) directamente en la Fourier inversa algebraica.')
                text=finite_definition(field.expression.text(),first,last)
                conditions.append('Las posiciones y pesos de Dirac se conservaron en precisión numérica, incluidos los impulsos de los extremos, sin multiplicarlos por una ventana ambigua.')
            else:text='Piecewise((('+text+'), ('+variable+'>=('+start+')) and ('+variable+'<=('+stop+'))), (0, True))'
            conditions.append('La definición se limita al intervalo de entrada '+start+' … '+stop+'. Dentro se integra la fórmula; el método numérico usa una cuadratura de sus muestras.')
        def copy_to_algebraic():
            dst.expression.setText(text)
            if discrete and not inverse:
                dst.lower.setText(field.origin.text());dst.upper.setText('('+field.origin.text()+')+('+field.count.text()+')-1')
            dst._expression_origin=(dst.expression.text(),_origin(field));dst._input_conditions=tuple(conditions);dst.input_id=_origin(field);dst.refresh_origin()
            if discrete and inverse:
                src_panel=getattr(source,'panel',None);dst.start.setText(src_panel.start.text());dst.count.setText(src_panel.count.text())
        return InputCopy([copy_to_algebraic], 'Se copiaron la fórmula y su soporte finito. Calculá aquí para obtener la expresión algebraica.' if not (discrete and inverse) else 'Se copiaron X(ω) y los índices de salida. La fórmula describe un período completo; calculá aquí para obtener x[n].')
    if dst is None:return None
    text=to_numeric(_support(field) if discrete and not inverse else field.expression.text())
    def copy_to_numeric():
        dst.mode.setCurrentIndex(0);dst.expression.setText(text)
        if dst.kind=='frequency':dst.frequency_units.setCurrentText('rad/muestra' if discrete else 'rad/s')
        dst._expression_origin=(dst.expression.text(),_origin(field));dst._expression_conditions=field._input_conditions if field._expression_origin and field._expression_origin[0]==field.expression.text() else ()
        if discrete and not inverse:
            try:
                lower=integer_field(field.lower);upper=integer_field(field.upper)
                if upper>=lower:dst.origin.setText(str(lower));dst.count.setText(str(upper-lower+1))
            except ValueError:pass  # Infinite support keeps the chosen observation window.
        if discrete and inverse:
            dst_panel=getattr(target,'panel',None);dst_panel.start.setText(field.start.text());dst_panel.count.setText(field.count.text())
    note='Se copiaron la fórmula y su soporte. Un soporte finito fija los índices; si es infinito, revisá la ventana de muestras antes de calcular.' if discrete and not inverse else 'Se copiaron X(ω) y los índices de salida. Se conserva la rejilla numérica de frecuencia.' if discrete else 'Se copió la fórmula completa. Revisá el inicio, la cantidad y el paso del intervalo finito de entrada antes de calcular; el resultado numérico aproxima esa ventana.'
    return InputCopy([copy_to_numeric],note)
