"""Mathematical expressions remain expressions in the result library."""
from dataclasses import dataclass

@dataclass(frozen=True)
class ExpressionResult:
    source:str
    variable:str|None
    conditions:tuple=()
    units:str=''
    numerical_source:str=''

def expression_result(value):
    if not isinstance(value,dict):return None
    cas=value.get('cas_answer')
    if isinstance(cas,dict):
        source=cas.get('expression');symbols=cas.get('symbols',[])
        symbols=sorted(set(symbols) | set(cas.get('domain_symbols',())))
        if not source:return None
        known=[v for v in symbols if v in ('n','t','s','z','w')]
        variable=cas.get('coordinate_variable') if not known and cas.get('coordinate_variable') else known[0] if len(known)==1 else 'mixed' if len(known)>1 else symbols[0] if len(symbols)==1 else None
        return ExpressionResult(source,variable,tuple(dict.fromkeys([*['Supuesto '+str(k)+': '+str(v) for k,v in cas.get('assumptions',[])],*map(str,cas.get('notices',[]))])),cas.get('frequency_units',''))
    result=value.get('result');request=value.get('request',{})
    if not isinstance(result,dict):return None
    if result.get('evaluated') is False:
        if result.get('boundary_dtft'):
            return ExpressionResult(result['boundary_dtft'],'w',tuple(str(result[k]) for k in ('roc','scope') if result.get(k)), 'rad/muestra')
        return None
    branches=result.get('branches',[])
    if len(branches)>1:return None
    source=branches[0].get('expression') if branches else result.get('transfer',result.get('result'))
    if not isinstance(source,str) or not source.strip():return None
    if result.get('display_result') and not result.get('display_numeric'):source=result['display_result']
    variable=result.get('output_variable')
    if 'transfer' in result and result.get('model_kind')!='frequency':variable='s' if request.get('domain')=='analog' else 'z'
    conditions=[str(result[k]) for k in ('roc','condition','frequency_condition','convergence','scope') if result.get(k) not in (None,'True','')]
    if result.get('cas_input_domain'):conditions.append(result['cas_input_domain'])
    if result.get('mathematical_conditions'):
        conditions.extend(label+': '+result['mathematical_conditions'][key] for key,label in [('domain','Dominio'),('causality','Causalidad'),('bibo_stability','Estabilidad BIBO')])
    if branches and branches[0].get('condition'):conditions.append(str(branches[0]['condition']))
    conditions.extend(str(value) for value in request.get('input_conditions',()))
    return ExpressionResult(source,variable,tuple(dict.fromkeys(conditions)),(result.get('frequency_units','') if variable=='w' else ''),result.get('display_result','') if result.get('display_numeric') else '')

def expression_destinations(expression):
    v=expression.variable;destinations=[('Copiar expresión','copy'),('Calculadora CAS','cas')]
    if v in ('n','t'):destinations += [('Crear señal '+('discreta' if v=='n' else 'continua'),'signal'),('Transformada '+('Z directa' if v=='n' else 'de Laplace directa'),'direct'),('Energía y potencia','measures')]
    if v in ('n','t'):destinations.append(('Transformar esta señal','transform_signal'))
    if v in ('n','t'):destinations.extend([('Sumar con otra señal','sum'),('Multiplicar por otra señal','product')])
    if v=='tau':destinations.append(('Crear señal continua desde la correlación','signal'))
    if v=='n':destinations.append(('Enventanar como h[n] de un FIR','fir_window'))
    if v in ('s','z'):destinations += [('Transformada '+('Z inversa' if v=='z' else 'de Laplace inversa'),'inverse'),('Analizar como H('+v+')','system')]
    if v=='w' and expression.units in ('rad/s','rad/muestra'):destinations.append(('Analizar respuesta en frecuencia','system'))
    if v=='w' and expression.units=='rad/s':destinations.append(('Fourier continua inversa','fourier_inverse'))
    if v=='w' and expression.units in ('','rad/muestra'):
        destinations.extend([('DTFT inversa algebraica','inverse_dtft'),('DTFT inversa numérica','inverse_dtft_numeric')])
    return destinations

def signal_source(source):
    """Mathematical spelling only, without evaluating or dropping conditions."""
    from .expression_dialects import to_numeric
    return to_numeric(source)


def check_cas_destination(answer,destination):
    if not answer.get('domain_condition') or destination in ('copy','cas'):
        return
    coordinate=answer.get('coordinate_variable')
    if coordinate in ('n','k','t','tau'):
        from .cas_context import coordinate_domain
        from .cas_engine import restore
        import sympy as sp
        condition=restore(answer['domain_condition'])
        if condition==sp.Contains(sp.Symbol(coordinate),coordinate_domain(coordinate)):return
    if destination in ('system','analog','digital','inverse') and answer.get('domain_condition_implicit'):
        return
    if destination in ('system','digital'):
        if answer.get('domain_condition_analysis'):return
        # Results saved before the analysis flag was introduced still have
        # their encoded domain condition.
        if answer.get('domain_symbols')==['z'] and answer.get('expression'):
            from .cas_engine import restore
            from .cas_domains import intrinsic_system_domain
            from .symbolic import parse
            try:
                if intrinsic_system_domain(parse(answer['expression']),restore(answer['domain_condition']),analysis=True):return
            except (SyntaxError,ValueError,TypeError):pass
    if destination in ('system','frequency') and answer.get('coordinate_variable')=='w' and answer.get('context_rewrite') is True:
        return
    raise ValueError('Este destino no aplica las condiciones de validez del CAS. Revisá la condición en el informe y definí allí el dominio antes de reutilizar la fórmula.')


def populate_reuse_menu(menu,window,key):
    if key is None:return
    expression=window.project.expression(key)
    if expression is None:return
    for label,destination in expression_destinations(expression):
        if destination=='cas':continue
        menu.addAction(label,lambda checked=False,target=destination:send_expression(window,key,target))


def send_expression(window,key,destination):
    from PySide6.QtWidgets import QApplication
    from .workspaces import ROUTES
    record=window.project.get(key)
    expression=expression_result(record)
    if expression is None:raise ValueError('Este resultado no contiene una expresión única evaluada.')
    check_cas_destination(record.get('cas_answer',{}),destination)
    text=expression.source;v=expression.variable
    if destination=='copy':QApplication.clipboard().setText(text);return
    if destination=='cas':
        from .cas_transfer import send_to_cas
        send_to_cas(window,key);return
    elif destination in ('direct','inverse'):
        if destination=='direct' and expression.numerical_source:text=expression.numerical_source
        route=ROUTES['transform_lab','z' if v in ('n','z') else 'laplace'];window.open_tool(route);panel=window.pages[window.current_operation].panel
        panel.mode.setCurrentIndex(1 if destination=='inverse' else 0)
        if destination=='direct' and v=='n':panel.direct_input.setCurrentIndex(0)
        panel.expression.setText(text)
        if v=='n':panel.lower.setText('-oo');panel.upper.setText('oo')
        if v in ('s','t'):
            stored=window.project.get(key);request=stored.get('request',{}) if isinstance(stored,dict) else {};result=stored.get('result',{}) if isinstance(stored,dict) else {}
            panel.load_laplace_context({'interpretation':'bilateral'} if v=='t' else request,result,inverse=v=='s')
        if destination=='inverse':panel.load_transform_context(window.project.get(key))
        panel._library_source=(text,key);panel._library_conditions=tuple(expression.conditions)
        panel.set_copy_note('Expresión cargada desde Resultados.'+(' Condiciones: '+'; '.join(expression.conditions) if expression.conditions else ''))
    elif destination=='system':
        window.open_tool(ROUTES['system_analysis',0]);panel=window.pages[window.current_operation].panel
        panel.load_expression(expression,key,window.project.get(key))
    elif destination=='transform_signal':
        window.open_tool(ROUTES['basic','shift'] if v=='n' else ROUTES['time_transform',0]);panel=window.pages[window.current_operation].panel;field=panel.source
        prepared=signal_source(expression.numerical_source or text);field.mode.setCurrentIndex(0);field.expression.setText(prepared);field._expression_origin=(field.expression.text(),key)
    elif destination in ('sum','product','fir_window'):
        prepared=signal_source(expression.numerical_source or text)
        if destination=='fir_window':
            window.open_tool(ROUTES['fir_window',0]);field=window.pages[window.current_operation].panel.h
        else:
            window.open_tool(ROUTES['basic','sum'] if destination=='sum' else ROUTES['signal_product',0]);panel=window.pages[window.current_operation].panel;panel.domain.setCurrentIndex(0 if v=='n' else 1);field=panel.first
        field.mode.setCurrentIndex(0);field.expression.setText(prepared);field._expression_origin=(field.expression.text(),key)
        if destination!='fir_window':panel.show_source(field)
    elif destination=='signal':
        if v=='tau':
            import re
            text=re.sub(r'\btau\b','t',text)
        window.open_tool(ROUTES['basic','generate']);page=window.pages[window.current_operation];page.source_domain.setCurrentIndex(0 if v=='n' else 1)
        prepared=signal_source(expression.numerical_source or text);page.first.mode.setCurrentIndex(0);page.first.expression.setText(prepared);page.first._expression_origin=(page.first.expression.text(),key)
    elif destination=='measures':
        window.open_tool(ROUTES['expression_measures','global']);panel=window.pages[window.current_operation].panel;panel.load_expression(expression,key)
    elif destination=='fourier_inverse':
        window.open_tool(ROUTES['fourier_symbolic',1]);panel=window.pages[window.current_operation].panel;panel.load_expression(expression,key)
    elif destination=='inverse_dtft':
        window.open_tool(ROUTES['dtft_symbolic',1]);panel=window.pages[window.current_operation].panel;panel.load_expression(expression,key)
    elif destination=='inverse_dtft_numeric':
        window.open_tool(ROUTES['inverse_dtft',0]);panel=window.pages[window.current_operation].panel
        prepared=signal_source(expression.numerical_source or text);panel.source.mode.setCurrentIndex(0);panel.source.frequency_units.setCurrentIndex(1);panel.source.expression.setText(prepared);panel.source._expression_origin=(panel.source.expression.text(),key)
    else:raise ValueError('Destino de expresión no disponible.')
    window.statusBar().showMessage('Expresión cargada desde Resultados. Revisá sus condiciones y calculá en el destino.')
