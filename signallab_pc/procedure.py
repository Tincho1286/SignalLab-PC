"""Serializable evidence from executed mathematical operations; no UI dependency."""
def step(title,operation,before=None,after=None,*,conditions='',interpretation='',source='',verification=None):
    value={'title':title,'operation':operation,'before':None if before is None else str(before),
           'after':None if after is None else str(after),'conditions':str(conditions),
           'interpretation':interpretation,'source':source,'recorded':True}
    if verification is not None:value['verification']=verification
    return value


def views(records):
    # Legacy title/text/formula fields remain supported by stored projects.
    result=[]
    for record in records:
        if not record.get('recorded'):
            result.append(dict(record));continue
        text=record['operation']
        if record.get('interpretation'):text+='\n\n'+record['interpretation']
        if record.get('conditions'):text+='\n\nValidez: '+record['conditions']
        result.append({'title':record['title'],'text':text,**({'formula':record['before']} if record.get('before') is not None else {})})
        if record.get('after') is not None:
            result.append({'title':'Expresión obtenida','text':'Salida almacenada de esta operación.','formula':record['after']})
    return result


def transform_records(request,result):
    """A calculation receipt, including only intermediates actually returned."""
    operation=request['operation'];inverse=operation.startswith('inverse') or operation=='z_inverse_expression'
    incoming=request.get('expression')
    input_scope='' if incoming is not None else 'Registro finito: '+str(len(request.get('samples',[])))+' muestras desde n='+str(request.get('origin',0))+'. Los datos permanecen en la entrada original.'
    conditions='; '.join([value for value in [input_scope,*[str(result[k]) for k in ('condition','roc','convergence','scope') if result.get(k)]] if value and value!='True'])
    records=[]
    if result.get('decomposition'):
        records.append(step('Descomposición registrada','Separación algebraica devuelta por el motor',incoming,result['decomposition'],conditions=conditions,source=operation))
        incoming=result['decomposition']
    for index,pair in enumerate(result.get('geometric_terms',[])):
        c,d,p,m=pair['coefficient'],pair['delay'],pair['pole'],pair['order'];q='(n-('+d+'))'
        value='('+c+')*impulse(n-('+d+'))' if p is None else '('+c+')*binomial('+q+'+'+str(m-1)+','+str(m-1)+')*('+p+')^'+q+'*step(n-('+d+'))' if pair['right'] else '('+c+')*(-1)^'+str(m)+'*binomial(-'+q+'-1,'+str(m-1)+')*('+p+')^'+q+'*step(('+d+')-'+str(m)+'-n)'
        records.append(step('Par geométrico almacenado '+str(index+1),'Término reconstruido con los parámetros registrados por la inversión',after=value,conditions=conditions,interpretation='Coeficiente '+c+' y desplazamiento '+d+(' muestras; soporte derecho.' if pair['right'] else ' muestras; soporte izquierdo.'),source=operation))
    branches=result.get('branches') or [{'expression':result.get('display_result',result.get('result'))}]
    for index,branch in enumerate(branches):
        output=branch.get('expression',branch.get('result'))
        if output is None:continue
        records.append(step(('Inversión' if inverse else 'Transformación')+' registrada'+(' · rama '+str(index+1) if len(branches)>1 else ''),
            'Evaluación de la transformada solicitada' if result.get('evaluated') else 'Intento de evaluación; permanecen operaciones sin resolver',incoming,output,
            conditions='; '.join(filter(None,[conditions,str(branch.get('condition',''))])),
            interpretation='Se conservan la entrada y la salida calculadas. No se atribuyen manipulaciones algebraicas intermedias que el motor no registre.',source=operation))
    return records
