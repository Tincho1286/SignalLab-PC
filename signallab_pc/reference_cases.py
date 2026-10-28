"""Ejecutor restringido de casos de referencia; sin eval ni importación desde datos."""
import json
from pathlib import Path
import numpy as np
from .model import Signal
from .filters import Transfer
from . import operations

def run_cases(document):
    if document.get('format')!='signallab-reference-cases' or document.get('schema_version')!=1:raise ValueError('Formato de casos incompatible.')
    cases=document.get('cases')
    if not isinstance(cases,list):raise ValueError('Lista de casos faltante.')
    ids=set();results=[]
    vector=lambda data:[complex(*value) for value in data]
    signal=lambda data:Signal(vector(data['values']),data.get('origin',0))
    for case in cases:
        key=case['id']
        if not isinstance(key,str) or key in ids:raise ValueError('Identificador de caso inválido o duplicado.')
        ids.add(key);op=case['operation']
        if op not in ('dft','idft','convolve','correlate','impulse'):raise ValueError('Operación de caso no admitida: '+str(op))
        atol=float(case['tolerance']['absolute']);rtol=float(case['tolerance']['relative'])
        if not np.isfinite([atol,rtol]).all() or atol<0 or rtol<0:raise ValueError('Tolerancia no válida.')
        try:
            data=case['input']
            if op=='impulse':actual=Transfer(vector(data['b']),vector(data['a'])).excitation_response(data['count'])
            elif op=='dft':actual=operations.dft(signal(data))
            elif op=='idft':actual=operations.idft(signal(data))
            elif op=='convolve':actual=operations.linear_convolution(signal(data),signal(case['second']))
            else:actual=operations.correlation(signal(data),signal(case['second']))
            expected=signal(case['expected'])
            np.testing.assert_allclose(actual.values,expected.values,atol=atol,rtol=rtol)
            if actual.origin!=expected.origin:raise AssertionError(f'Origen {actual.origin}, esperado {expected.origin}')
            results.append({'id':key,'status':'passed','max_absolute_error':float(np.max(abs(actual.values-expected.values)))})
        except Exception as exc:results.append({'id':key,'status':'failed','error':str(exc)})
    return {'format':'signallab-case-results','schema_version':1,'platform':'pc','all_passed':bool(results) and all(r['status']=='passed' for r in results),'results':results,'scope':'Sólo los casos indicados; no afirma resultados HP ni paridad total.'}

def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('cases');parser.add_argument('--output',required=True);args=parser.parse_args(argv)
    result=run_cases(json.loads(Path(args.cases).read_text(encoding='utf-8-sig')))
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Casos aprobados: '+str(result['all_passed']));return 0 if result['all_passed'] else 1

if __name__=='__main__':raise SystemExit(main())
