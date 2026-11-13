"""Register complete successful tool outputs in the shared result library."""
from dataclasses import fields,is_dataclass
import math
import numpy as np
from .model import Signal
from .filters import Transfer
from .state_space import StateModel
from .project import encode

TYPED=(Signal,Transfer,StateModel)

def typed_outputs(value,seen=None):
    seen=set() if seen is None else seen
    if id(value) in seen:return
    seen.add(id(value))
    if isinstance(value,TYPED):yield value
    elif isinstance(value,dict):
        for item in value.values():yield from typed_outputs(item,seen)
    elif isinstance(value,(tuple,list)):
        for item in value:yield from typed_outputs(item,seen)
    elif is_dataclass(value):
        for field in fields(value):yield from typed_outputs(getattr(value,field.name),seen)

def snapshot(value,window):
    if isinstance(value,TYPED):
        key=window.published_value_id(value)
        if key:
            journal=getattr(window,'_result_journal',None)
            if journal:journal.references.add(key)
            return {'result_id':key}
        kind,data=encode(value);return {'type':kind,'data':data}
    if isinstance(value,np.ndarray):
        from .resources import ensure_working_set
        ensure_working_set(value.size,bytes_per_sample=96,live_arrays=3)
        values=value.reshape(-1)
        data=[[snapshot(v.real,window),snapshot(v.imag,window)] for v in values] if np.iscomplexobj(value) else [snapshot(v,window) for v in values]
        return {'shape':list(value.shape),'dtype':str(value.dtype),'values':data}
    if isinstance(value,np.generic):return snapshot(value.item(),window)
    if isinstance(value,complex):return {'real':snapshot(value.real,window),'imag':snapshot(value.imag,window)}
    if isinstance(value,float) and not math.isfinite(value):return {'nonfinite':'NaN' if math.isnan(value) else '+infinity' if value>0 else '-infinity'}
    if value is None or isinstance(value,(bool,int,float,str)):return value
    if isinstance(value,dict):return {str(k):snapshot(v,window) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [snapshot(v,window) for v in value]
    if is_dataclass(value):return {'type':type(value).__name__,**{f.name:snapshot(getattr(value,f.name),window) for f in fields(value)}}
    return {'type':type(value).__name__,'expression':str(value)}

def result_description(value):
    if isinstance(value,TYPED):return getattr(value,'name','Resultado')
    if isinstance(value,np.ndarray):return 'Tabla '+str(value.shape)+' · '+str(value.dtype)+'. Valores completos en la exportación JSON.'
    if isinstance(value,dict):return '\n'.join(str(k)+': '+result_description(v) for k,v in value.items())
    if isinstance(value,(tuple,list)):
        preview='\n'.join(str(i+1)+'. '+result_description(v) for i,v in enumerate(value[:8]))
        return 'Lista de '+str(len(value))+' elementos\n'+preview+('\nVista parcial; datos completos conservados en el cálculo.' if len(value)>8 else '')
    if is_dataclass(value):return '\n'.join(f.name+': '+result_description(getattr(value,f.name)) for f in fields(value))
    return str(value)

class ResultJournal:
    def __init__(self,window,message):
        self.window=window;route=getattr(window,'current_operation',None)
        self.origin={'title':route[0] if route else message,'route':list(route) if route else []}
        self.title=self.origin['title'];self.records=[];self.values=[];self.references=set();self.result=None;self.whole_result_stored=False
        page=window.pages.get(route);panel=getattr(page,'panel',None)
        if getattr(panel,'calculation_title',None):self.title=self.origin['title']=panel.calculation_title
        from .report_view import ReportView
        self.page=page;self.calculation_notes=[]
        views=list(page.findChildren(ReportView)) if page is not None else []
        views.extend(view for view in (getattr(page,'report',None),getattr(panel,'report',None)) if view is not None)
        self.reports={view:view.toPlainText() for view in views}
        self.report_versions={view:getattr(view,'_report_revision',0) for view in self.reports}
    def enrich(self,value):
        from .calculation_notes import plain_text
        if self.calculation_notes:
            if isinstance(value,Signal):value.metadata['calculation_notes']=self.calculation_notes
            elif isinstance(value,dict):
                value={**value,'calculation_notes':self.calculation_notes}
                if isinstance(value.get('report'),str) and 'Levantamiento de indeterminaciones' not in value['report']:value['report']=plain_text(self.calculation_notes)+'\n\n'+value['report']
        if isinstance(value,dict) and isinstance(value.get('report'),str) and 'calculated_data' not in value:
            self.whole_result_stored=True
            return {**value,'calculated_data':snapshot(self.result,self.window)}
        return value
    def published(self,key,value):
        self.records.append(key);self.values.append(value)
        if value is self.result or isinstance(value,dict) and value.get('result') is self.result:self.whole_result_stored=True
    def accept(self,result,callback):
        self.result=result;previous=getattr(self.window,'_result_journal',None);self.window._result_journal=self
        try:
            try:callback(result)
            except Exception:
                self.collect(result)
                raise
            self.window._last_calculation_notes=self.calculation_notes
            from .report_view import ReportView
            views=list(self.page.findChildren(ReportView)) if self.page is not None else []
            for view in set([*self.reports,*views]):
                if getattr(view,'_raw','') and getattr(view,'_report_revision',0)!=self.report_versions.get(view,-1) and hasattr(view,'set_calculation_notes'):view.set_calculation_notes(self.calculation_notes)
            self.collect(result)
            if self.calculation_notes:
                from .calculation_notes import plain_text
                self.window.publish({'report':plain_text(self.calculation_notes),'calculation_notes':self.calculation_notes},title='Indeterminaciones · '+self.title,operation='Levantamiento de indeterminaciones',parents=self.records[:])
        finally:
            self.window._result_journal=previous
            if previous is None:self.window.refresh_project()
    def reported(self,result):
        # A compact published report may retain input IDs rather than copies.
        if result is self.result:self.whole_result_stored=True

    def collect(self,result):
        if isinstance(result,dict) and 'error' in result:return
        # Scalar CAS answers are explicitly published without worksheet state.
        if len(self.origin['route'])>1 and self.origin['route'][1]=='cas':return
        for value in typed_outputs(result):
            if self.window.published_value_id(value) is None:self.window.publish(value,operation=self.title,parents=self.records[:])
        def only_typed(value):
            if value is None or isinstance(value,TYPED):return True
            if isinstance(value,(tuple,list)):return all(only_typed(v) for v in value)
            return False
        if not self.whole_result_stored and not only_typed(result):
            report='\n\n'.join(view.toPlainText() for view,old in self.reports.items() if view.toPlainText()!=old)
            self.window.publish({'report':report or result_description(result),'calculated_data':snapshot(result,self.window)},title=self.title,operation=self.title,parents=self.records[:])
