"""Conserva la realización importada mientras no se edita su definición."""
from .filters import Transfer
from .systems_panel import parse_list

def remember_system(editor,system):
    if hasattr(editor,'definition_mode'):editor.definition_mode.setCurrentIndex(0)
    editor._preserved_system=system
    editor._preserved_definition=(editor.b.text(),editor.a.text(),editor.domain.currentIndex())
    editor._preserved_formula=None
    if system.advance and hasattr(editor,'transfer_formula'):
        from .phase_summary import transfer_formula
        expression=transfer_formula(system,digits=17)[0].text.split('=',1)[1].strip()
        editor.transfer_formula.setText(expression);editor.definition_mode.setCurrentIndex(1)
        editor._preserved_formula=(expression,editor.domain.currentIndex())
    from .system_clock import remember_period
    remember_period(editor,system.sample_period_s)

def read_system(editor,digital_index=1,name='Sistema de entrada',allow_advance=False):
    from .system_clock import editor_period,apply_period
    return apply_period(_read_system(editor,digital_index,name,allow_advance),editor_period(editor))

def _read_system(editor,digital_index=1,name='Sistema de entrada',allow_advance=False):
    if hasattr(editor,'definition_mode') and editor.definition_mode.currentIndex()==1:
        if (editor.transfer_formula.text(),editor.domain.currentIndex())==getattr(editor,'_preserved_formula',None):
            result=editor._preserved_system
            if result.advance and not allow_advance:raise ValueError('Este sistema conserva un avance temporal. Esta herramienta utiliza realizaciones causales; su análisis completo está disponible en Análisis de sistemas y Z inversa con ROC.')
            return result
        return formula_system(editor.transfer_formula.text(),'digital' if editor.domain.currentIndex()==digital_index else 'analog',name,allow_advance=allow_advance)
    definition=(editor.b.text(),editor.a.text(),editor.domain.currentIndex())
    if definition==getattr(editor,'_preserved_definition',None):
        result=editor._preserved_system
        if result.advance and not allow_advance:raise ValueError('La definición contiene un avance temporal; usá Análisis de sistemas o Z inversa con ROC.')
        return result
    return Transfer(parse_list(editor.b.text()),parse_list(editor.a.text()),'digital' if editor.domain.currentIndex()==digital_index else 'analog',name)


def formula_system(expression,domain,name='Sistema definido por fórmula',allow_advance=False):
    from .symbolic_process import run_request
    result=run_request({'operation':'system_formula','expression':expression,'domain':domain})
    if 'numeric_b' not in result:raise ValueError('Asigná valores a los parámetros antes de simular el sistema.')
    if result.get('advance',0) and not allow_advance:raise ValueError('Esta fórmula contiene un avance temporal. Podés analizarla en Sistemas LTI → Función de transferencia y análisis; esta operación causal requiere un sistema sin avances.')
    return Transfer([complex(*v) for v in result['numeric_b']],[complex(*v) for v in result['numeric_a']],domain,name,advance=result.get('advance',0))


def install_formula_editor(editor,form):
    from PySide6.QtWidgets import QComboBox,QLineEdit
    if hasattr(editor,'definition_mode'):return
    editor.definition_mode=QComboBox();editor.definition_mode.addItems(['Coeficientes','Fórmula H(s) / H(z)'])
    editor.transfer_formula=QLineEdit('1/(s+1)' if editor.domain.currentIndex()==0 else '1/(1-0.5*z^(-1))')
    from .choice_buttons import ChoiceButtons
    editor.definition_buttons=ChoiceButtons(editor.definition_mode,['Coeficientes','Fórmula H'])
    form.insertRow(0,editor.definition_buttons);form.insertRow(1,'H(s) o H(z)',editor.transfer_formula)
    def update(*_):
        definition=getattr(editor,'fields',{}).get('definition')
        ideal=definition is not None and definition.currentData()=='response'
        formula=editor.definition_mode.currentIndex()==1
        form.setRowVisible(editor.definition_buttons,not ideal);form.setRowVisible(editor.transfer_formula,formula and not ideal)
        form.setRowVisible(editor.b,not formula and not ideal);form.setRowVisible(editor.a,not formula and not ideal)
        if hasattr(editor,'preview'):form.setRowVisible(editor.preview,not formula and not ideal)
    def change_default(*_):
        if editor.transfer_formula.text() in ('1/(s+1)','1/(1-0.5*z^(-1))'):
            editor.transfer_formula.setText('1/(s+1)' if editor.domain.currentIndex()==0 else '1/(1-0.5*z^(-1))')
    editor.domain.currentIndexChanged.connect(change_default)
    editor.definition_mode.currentIndexChanged.connect(update)
    if 'definition' in getattr(editor,'fields',{}):editor.fields['definition'].currentIndexChanged.connect(update)
    update()
