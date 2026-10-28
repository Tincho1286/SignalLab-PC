"""Prepare compatible input copies without evaluating or changing either draft."""
from dataclasses import dataclass,field

@dataclass
class InputCopy:
    actions:list=field(default_factory=list)
    note:str='Estas vistas usan entradas diferentes; cada una conserva sus propios datos.'
    def apply(self):
        try:
            for action in self.actions:action()
        except (ValueError,MemoryError,OverflowError) as exc:return 'La copia no se completó. Revisá los datos de esta vista antes de calcular. '+str(exc)
        return self.note

def copy_local_input(src,dst):
    from copy import deepcopy
    loaded=deepcopy(src.loaded) if src.mode.currentIndex()==2 and src.loaded is not None else None
    for name in ('expression','samples','origin','count','step'):getattr(dst,name).setText(getattr(src,name).text())
    if hasattr(src,'frequency_units') and hasattr(dst,'frequency_units'):dst.frequency_units.setCurrentIndex(src.frequency_units.currentIndex())
    if src.mode.currentIndex()==2:
        if src.loaded is not None:dst.set_source(loaded,src.loaded_reference_id)
        else:
            dst.loaded=None;dst.reference_id=None;dst.loaded_reference_id=None;dst.fingerprint=None;dst.mode.setCurrentIndex(2)
            dst.file_note.setText('Elegí un archivo o un resultado anterior. Todavía no hay datos cargados.');dst.source_revision=getattr(dst,'source_revision',0)+1;dst.sourceChanged.emit()
    else:dst.mode.setCurrentIndex(src.mode.currentIndex())
    origin=getattr(src,'_expression_origin',None)
    dst._expression_origin=(dst.expression.text(),origin[1]) if origin and origin[0]==src.expression.text() else None
    dst._expression_conditions=getattr(src,'_expression_conditions',()) if dst._expression_origin else ();dst.fingerprint=None

def prepare_inputs(source,target):
    from .toolbox import LocalInput
    a=getattr(source,'panel',None);b=getattr(target,'panel',None);actions=[]
    def assign(dst,src):actions.append(lambda:dst.setText(src.text()))
    from .fourier_workflow import prepare_fourier_inputs
    try:plan=prepare_fourier_inputs(source,target)
    except (SyntaxError,ValueError) as exc:return InputCopy(note='La definición está incompleta o no se puede copiar todavía. Se conservó la entrada de esta vista. '+str(exc))
    if plan is not None:return plan
    if a is not None and b is not None:
        if a.__class__.__name__==b.__class__.__name__=='SignalProductPanel':
            domain=a.domain.currentIndex()
            def arithmetic():
                b.domain.setCurrentIndex(domain)
                for src,dst in zip(a.inputs[domain],b.inputs[domain]):copy_local_input(src,dst)
                b.input_tabs[domain].setCurrentIndex(a.input_tabs[domain].currentIndex())
            return InputCopy([arithmetic],'Se copiaron las dos entradas y su dominio. Las opciones y el último resultado de esta operación se conservan; calculá para actualizarlo.')
    if a is not None and b is not None and hasattr(a,'band_edges') and hasattr(b,'band_edges'):
        if a.band_edges.analog!=b.band_edges.analog:return InputCopy(note='Se conserva la entrada de este dominio: rad/s y rad/muestra no se convierten automáticamente.')
        actions.append(lambda:b.band_edges.kind.setCurrentIndex(b.band_edges.kind.findData(a.band_edges.kind.currentData())))
        for src,dst in zip(a.band_edges.edits,b.band_edges.edits):assign(dst,src)
        for name in ('dp','ds'):assign(b.fields[name],a.fields[name])
    if a is not None and b is not None and a.__class__.__name__==b.__class__.__name__=='StateSpacePanel':
        if b.action=='discretize' and a.domain.currentIndex()==1:return InputCopy(note='Discretizar necesita un modelo continuo. Se conserva la entrada continua de esta vista.')
        actions.append(lambda:b.domain.setCurrentIndex(a.domain.currentIndex()));assign(b.step,a.step)
        for name in ('A','B','C','D'):assign(b.fields[name],a.fields[name])
        actions.append(lambda:setattr(b,'model_parent',a.model_parent));actions.append(lambda:setattr(b,'_model_name',getattr(a,'_model_name','Sistema de estados')))
    if a is not None and b is not None and a.__class__.__name__==b.__class__.__name__=='ExpressionMeasuresPanel':
        actions.append(lambda:b.domain.setCurrentIndex(a.domain.currentIndex()));assign(b.expression,a.expression)
        def measure_origin():
            origin=getattr(a,'_expression_origin',None)
            intact=origin and origin[0]==a.expression.text() and origin[2]==a.domain.currentIndex()
            b._expression_origin=(b.expression.text(),origin[1],b.domain.currentIndex()) if intact else None
            b.parent_id=origin[1] if intact else None;b._input_conditions=a._input_conditions if intact else ();b.refresh_origin()
        actions.append(measure_origin)
    if all(hasattr(panel,name) for panel in (a,b) for name in ('b','a','domain')):
        if any(getattr(panel,'action',None)=='phase' and panel.fields['phase_mode'].currentData()=='reconstruct' for panel in (a,b)):
            return InputCopy(note='Reconstruir usa datos de módulo o fase independientes de H(z). Se conserva la entrada de cada estudio.')
        if getattr(b,'action',None)=='phase' and a.domain.currentIndex()==0:return InputCopy(note='Fase y compensación necesita H(z). Se conserva su entrada digital; H(s) no se convierte automáticamente.')
        from .system_clock import editor_period,remember_period,UNSET
        try:source_period=editor_period(a)
        except ValueError:return InputCopy(note='El período T está incompleto o no es válido. Revisalo antes de copiar la definición a esta vista.')
        preserved=None;mode=getattr(a,'definition_mode',None)
        if mode is not None and mode.currentIndex()==1:
            if getattr(a,'_preserved_formula',None)==(a.transfer_formula.text(),a.domain.currentIndex()):preserved=a._preserved_system
        elif getattr(a,'_preserved_definition',None)==(a.b.text(),a.a.text(),a.domain.currentIndex()):preserved=a._preserved_system
        if preserved is not None and preserved.advance and (b.__class__.__name__=='TemporalPanel' or getattr(b,'action',None)=='phase'):return InputCopy(note='Esta vista usa una realización causal. Se conserva su entrada; el avance puede estudiarse en frecuencia o Z inversa.')
        def transfer():
            for name in ('_preserved_definition','_preserved_formula','_preserved_system'):setattr(b,name,None)
            b.domain.setCurrentIndex(a.domain.currentIndex());b.b.setText(a.b.text());b.a.setText(a.a.text())
            if hasattr(a,'definition_mode') and hasattr(b,'definition_mode'):
                b.transfer_formula.setText(a.transfer_formula.text());b.definition_mode.setCurrentIndex(a.definition_mode.currentIndex())
            if preserved is not None:
                from .transfer_input import remember_system
                from copy import deepcopy
                remember_system(b,deepcopy(preserved))
                if mode is not None and mode.currentIndex()==1 and hasattr(b,'definition_mode'):
                    b.transfer_formula.setText(a.transfer_formula.text());b.definition_mode.setCurrentIndex(1)
                    b._preserved_formula=(b.transfer_formula.text(),b.domain.currentIndex())
            period=source_period if source_period is not UNSET else preserved.sample_period_s if preserved is not None else None
            remember_period(b,period)
            parent=getattr(a,'input_id',getattr(a,'parent_id',None))
            for name in ('input_id','parent_id'):
                if hasattr(b,name):setattr(b,name,parent)
        actions.append(transfer)
    def role(page):
        key=page.tool_item[1:3]
        return 'dft_coefficients' if key==('basic','idft') else 'series_coefficients' if key==('course_tools','lines') else 'ordinary_signal'
    if role(source)==role(target):
        sources=[x for x in source.findChildren(LocalInput) if x.isVisibleTo(source)]
        targets=[x for x in target.findChildren(LocalInput) if x.isVisibleTo(target)];used=set()
        for dst in targets:
            src=next((x for i,x in enumerate(sources) if i not in used and x.kind==dst.kind),None)
            if src is None:continue
            used.add(sources.index(src))
            def local(src=src,dst=dst):copy_local_input(src,dst)
            actions.append(local)
    return InputCopy(actions,'Se copió la entrada. Las opciones propias de esta vista y su último resultado se conservan; calculá aquí para actualizarlo.') if actions else InputCopy()

def copy_inputs(source,target):return prepare_inputs(source,target).apply()
