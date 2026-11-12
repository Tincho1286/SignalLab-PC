"""Compare FIR windows using one specification and one measurement contract."""
from time import perf_counter
import csv
from .jobs import checkpoint

WINDOWS={'kaiser':'Kaiser','hann':'Hann','hamming':'Hamming','blackman':'Blackman','bartlett':'Bartlett','boxcar':'Rectangular'}


def compare(wp,ws,dp,ds,windows,*,mode='tolerances',length=65,amplitudes=(1,),units='absolute'):
    from .amplitude_design import design,limits
    from .course_tools import bands
    from .scalar_expression import integer_value
    wp,ws,kind=bands(wp,ws);limits(kind,amplitudes,dp,ds,units)
    windows=list(dict.fromkeys(windows))
    if not windows or any(window not in WINDOWS for window in windows):raise ValueError('Elegí al menos una ventana admitida para comparar.')
    if mode not in ('length','tolerances'):raise ValueError('Elegí igual longitud o iguales tolerancias.')
    fixed=None
    if mode=='length':
        if isinstance(length,bool):raise ValueError('La longitud común debe ser un entero positivo.')
        fixed=integer_value(length)
        if fixed<1:raise ValueError('La longitud común debe ser positiva.')
        if kind in ('highpass','bandstop') and fixed%2==0:
            raise ValueError('Estas bandas requieren paso en π. Las ventanas simétricas necesitan longitud impar; elegí L impar.')
    systems=[];rows=[];spec=None
    for window in windows:
        checkpoint();begin=perf_counter()
        try:
            result=design(wp,ws,dp,ds,'kaiser',window=window,amplitudes=amplitudes,units=units,fixed_length=fixed)
            system=result['systems'][0];metadata=result['fir_metadata'];metrics=result['specification_metrics'];spec=result['specifications']
            system.name='FIR '+WINDOWS[window]+' · L='+str(metadata['length'])
            passing=metrics['passing'] if metrics else []
            deviations=[max(abs(v['minimum']-a),abs(v['maximum']-a)) for v,a in zip(passing,spec['amplitudes'])]
            stop=max((v['maximum'] for v in metrics['stopping']),default=0.) if metrics else None
            margin=min([v['minimum']-lo for v,lo in zip(passing,spec['pass_lower'])]+[hi-v['maximum'] for v,hi in zip(passing,spec['pass_upper_bands'])]+[spec['stop_upper']-stop]) if metrics else None
            row=dict(window=window,name=WINDOWS[window],system_index=len(systems),length=metadata['length'],order=metadata['order'],
                     fir_type=metadata['type'],delay=metadata['delay'],beta=metadata['beta'] if window=='kaiser' else None,
                     pass_deviation=max(deviations) if deviations else None,stop_maximum=stop,margin=margin,
                     met=bool(result['specification_met']),metrics=metrics,report=result['report'],error=None)
            systems.append(system)
        except ValueError as exc:
            row=dict(window=window,name=WINDOWS[window],system_index=None,length=None,order=None,fir_type=None,delay=None,beta=None,
                     pass_deviation=None,stop_maximum=None,margin=None,met=False,metrics=None,report='',error=str(exc))
        row['seconds']=perf_counter()-begin;rows.append(row)
    scope=('Todas las ventanas utilizan L='+str(fixed)+'. El informe indica cuáles cumplen los límites; tener la misma longitud no garantiza el mismo rechazo.' if fixed is not None else
           'Cada ventana busca su primera longitud que supera la comprobación numérica con las mismas bandas, amplitudes y tolerancias. No es una certificación analítica de orden mínimo.')
    data=dict(mode=mode,length=fixed,rows=rows,scope=scope)
    summary=comparison_summary(data)
    return dict(systems=systems,signals=[],comparison=True,fir_comparison=data,specifications=spec,
                specification_met=all(row['met'] for row in rows),fir_summary=summary,report=summary.plain_text())


def comparison_summary(data):
    from .result_summary import Summary,Section,number
    sections=[Section('Criterio común',paragraphs=[data['scope'],'Las bandas de transición no se incluyen en las tolerancias. Kaiser obtiene β de esos límites. Los errores de paso y rechazo se expresan en amplitud lineal; el retardo está en muestras.'])]
    for row in data['rows']:
        if row['error']:
            sections.append(Section(row['name'],paragraphs=['No se obtuvo un diseño: '+row['error']]));continue
        measurements=[('Longitud L',str(row['length'])),('Orden nominal M=L−1',str(row['order'])),('FIR simétrico · tipo',row['fir_type']),
                      ('Retardo D',number(row['delay'])+' muestras'),('Tiempo de diseño y medición',number(row['seconds'])+' s'),
                      ('Estado','Dentro de tolerancias numéricas' if row['met'] else 'Fuera de tolerancias o con mediciones pendientes')]
        if row['beta'] is not None:measurements.append(('β de Kaiser',number(row['beta'])))
        for key,label in [('pass_deviation','Desvío máximo respecto de la amplitud de paso'),('stop_maximum','Máximo módulo en rechazo'),('margin','Menor margen frente a los límites')]:
            if row[key] is not None:measurements.append((label,number(row[key])))
        sections.append(Section(row['name'],rows=measurements))
        if row['metrics']:
            for category,title in [('passing','Paso'),('stopping','Rechazo')]:
                for i,band in enumerate(row['metrics'][category],1):
                    sections.append(Section(row['name']+' · '+title+' '+str(i),rows=[
                        ('Mínimo |H|',number(band['minimum'])),('En ω',number(band['minimum_at'])+' rad/muestra'),
                        ('Máximo |H|',number(band['maximum'])),('En ω',number(band['maximum_at'])+' rad/muestra')]))
        else:sections.append(Section('Detalle',paragraphs=[row['report']]))
    sections.append(Section('Uso de la comparación',paragraphs=['Elegí una fila para seleccionar el filtro. Graficar puede superponer los diseños sobre las mismas frecuencias; exportar y reutilizar toman el filtro elegido. La tabla CSV conserva también los intentos sin diseño y su motivo.']))
    return Summary('Comparación FIR por ventanas',sections)


def export_csv(data,path):
    columns=['Ventana','L','M','Tipo FIR','Retardo (muestras)','Beta Kaiser','Desvío máximo paso (amplitud)','Máximo rechazo (amplitud)','Margen mínimo (amplitud)','Tiempo (s)','Cumple','Observación']
    with open(path,'w',newline='',encoding='utf-8-sig') as target:
        writer=csv.writer(target,delimiter=';');writer.writerow(columns)
        for r in data['rows']:
            writer.writerow([r['name'],r['length'],r['order'],r['fir_type'],r['delay'],r['beta'],r['pass_deviation'],r['stop_maximum'],r['margin'],r['seconds'],'Sí' if r['met'] else 'No',r['error'] or 'Evaluación numérica por bandas'])
