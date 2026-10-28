"""Contrato de capacidades entre plataformas; referencias no implican paridad."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from . import __version__
from .navigation import MENUS
from .hp_inventory import source_inventory

FORMAT='signallab-capabilities'
SCHEMA=1
# Entradas de referencia revisadas por familia. Las subopciones conservan estado pendiente.
HP_CALLERS={
 'expression_measures:interval':['UISignalMeasures','SSMeasureResults'],
 'expression_measures:global':['UISignalMeasuresTheory','SSMeasureResults'],
 'expression_measures:periodic':['UISignalMeasures','SSMeasureResults'],
 'signal_editor:0':['UISampleExpr','SSShow'],
 'basic:generate':['UIGenerator','UISampleExpr'],
 'basic:measures':['UISignalMeasures','SSMeasureResults'],
 'basic:shift':['UITransformSignal'],'basic:reverse':['UITransformSignal'],'basic:scale':['UITransformSignal'],'basic:parity':['UITransformSignal'],'basic:sum':['UITransformSignal'],
 'basic:continuous_convolve':['UIContinuousConv','SSConvContinuousResults'],
 'convolution_algebra:0':['UIContinuousConv','SSConvContinuousResults'],
 'correlation_algebra:0':['UICorrelation'],'correlation:0':['UICorrelation'],'correlation:1':['UICorrelation'],
 'basic:convolve':['UIConvolution','SSConvDiscreteResults'],'basic:circular':['UIConvDFT','SSConvDFTResults'],
 'basic:dft':['UIDFT','SSDFTResults'],'basic:idft':['UIDFT','SSDFTResults'],
 'dtft_symbolic:0':['UIDFT'],'fourier_symbolic:0':['UIFourierContinuous'],'fourier_symbolic:1':['UIFourierContinuous'],
 'fourier:0':['UIDFT'],'fourier:1':['UIFourierContinuous'],'fourier:3':['UIFourierContinuous'],'fourier:4':['UIFourierContinuous'],'fourier:5':['UIDiscreteFourierSeries'],
 'fourier:6':['UISpectrum'],'fourier:7':['UISpectrum'],
 'system_analysis:0':['UIPolesZeros','SSCASRunTransform'],
 'systems:0':['UIFIRDesign','SSDigitalFilterResults'],'systems:1':['UIBiquadDesign','SSDigitalFilterResults'],'systems:2':['UIAnalogRCDesign','SSAnalogFilterResults'],
 'systems:3':['UIDiffEquation','UIPolesZeros'],'systems:4':['UIFreqResponse','UIBodeContinuous','UIFreqResponseContinuousLinear'],
 'systems:5':['UIApplyFilter','UIResponses','UIDiffEquation'],'systems:6':['UIPolesZeros','SSPlotPZ'],'systems:7':['UIBilinear'],
 'systems:8':['UISecondOrder'],'systems:9':['UISecondOrder','UIResponses'],'systems:10':['UIFeedback'],'systems:11':['UIRootLocus'],
 'rational_resampling:0':['UIRateChange','SSRateResults'],'sampling:0':['UISampleExpr','SSSampleResults'],'sampling:1':['UINyquist'],
 'sampling:2':['UIRateChange','SSRateResults'],'sampling:3':['UIReconstruction'],'sampling:4':['UIQuantization','SSQuantResults'],'sampling:5':['UIFixedPoint'],
 'symbolic:0':['SSCASRunTransform','UI_TRANSFORMS'],'symbolic:1':['SSCASRunTransform','UI_TRANSFORMS'],'symbolic:2':['UIZTransform'],'symbolic:3':['UIZTransform'],'symbolic:4':['UIODESolve'],
}
CONVENTIONS={
 'signal.finite.complex.v1':{'description':'Muestras complejas finitas; origen, paso, unidades y dominio explícitos. Una distribución no se representa como muestra finita.'},
 'transform.dft.v1':{'description':'DFT directa sin factor 1/N, inversa con 1/N; kernel exp(-j*2*pi*k*m/N), m=posición almacenada desde cero. No aplica fase por origen global. Salida IDFT desde n=0; bins DFT en orden sin centrar.'},
 'system.transfer.v1':{'description':'Digital: coeficientes ascendentes en z^-1. Analógico: descendentes en s. No se cancelan polos/ceros por tolerancia implícita.'},
 'correlation.complex.v1':{'description':'r_xh(lag)=sum/integral x(t)*conj(h(t-lag)); escala y soporte finito/periódico explícitos.'},
 'state_space.numeric.v1':{'description':'Continuo dx/dt=Ax+Bu; discreto x[k+1]=Ax[k]+Bu[k]; y=Cx+Du. Frecuencia en rad/s y z=exp(j*w*T). Simulación continua con entrada ZOH.'},
 'fourier.angular.v1':{'description':'X(w)=integral x(t) exp(-j*w*t) dt; inversa 1/(2*pi) integral X(w) exp(j*w*t) dw. w en rad/s. La cuadratura numérica es aproximación de un registro finito.'},
 'transform.dtft.v1':{'description':'X(w)=sum x[n] exp(-j*w*n), con índices originales; w en rad/muestra. No confundir con DFT de posiciones almacenadas.'},
 'sampling.clock.v1':{'description':'Periodo T en segundos, tasa Fs=1/T en Hz. Conservar origen temporal; expansión por ceros y remuestreo filtrado son operaciones distintas.'},
 'signal.measures.v1':{'description':'Energía como suma/integral de |x|². Potencia global: límite simétrico, normalizado por 2M+1 en discreto y 2R en continuo. Promedio de ventana y energía total son cantidades distintas. Un periodo se usa sólo tras demostrar periodicidad.'},
 'symbolic.conditions.v1':{'description':'Expresión original, resultado, condiciones y estado evaluado se conservan. Resultado simbólico pendiente no equivale a cero.'},
}

def capability_id(item):return f'tool.{item[1]}.{item[2]}'

def convention_ids(kind,index):
    symbolic=kind in ('expression_measures','symbolic','system_analysis','convolution_algebra','correlation_algebra','fourier_symbolic','dtft_symbolic')
    result=['symbolic.conditions.v1'] if symbolic else ['signal.finite.complex.v1']
    if kind=='expression_measures':result+=['signal.measures.v1']
    if kind=='state_space':result+=['state_space.numeric.v1','system.transfer.v1']
    if kind in ('systems','system_analysis'):result+=['system.transfer.v1']
    if kind=='basic' and index in ('dft','idft') or kind=='fourier' and index in (0,5):result+=['transform.dft.v1']
    if kind=='fourier_symbolic' or kind=='fourier' and index in (1,3,4):result+=['fourier.angular.v1']
    if kind=='dtft_symbolic' or kind=='fourier' and index==0:result+=['transform.dtft.v1']
    if 'correlation' in kind:result+=['correlation.complex.v1']
    if kind in ('sampling','rational_resampling'):result+=['sampling.clock.v1']
    return result

def build_catalog(hp_bytes):
    hp=source_inventory(hp_bytes);capabilities=[]
    cases=json.loads((Path(__file__).parent/'assets'/'reference-cases.json').read_text(encoding='utf-8-sig'))['cases']
    for category,items in MENUS.items():
        for item in items:
            title,kind,index,input_kind=item;callers=HP_CALLERS.get(f'{kind}:{index}',[])
            capabilities.append({'id':capability_id(item),'title':title,'category':category,'route':list(item),'input_kind':input_kind,
                'status':'pc_extension' if kind=='state_space' else 'partial_unreviewed_parity',
                'hp_callers':callers,'hp_menu_ids':[m['id'] for m in hp['menus'] if m['caller'] in callers],
                'relation':'related_behavior_not_equivalence','convention_ids':convention_ids(kind,index),
                'evidence':[{'case_id':case['id'],'scope':'Reference definition; execution evidence is reported separately.'} for case in cases if case['capability_id']==capability_id(item)],'remaining':'Auditar cada opción HP relacionada y sus condiciones; la existencia de una ruta PC no demuestra equivalencia.'})
    for menu in hp['menus']:
        menu['related_pc_ids']=[c['id'] for c in capabilities if menu['id'] in c['hp_menu_ids']]
    result={'format':FORMAT,'schema_version':SCHEMA,'platform':'pc','version':__version__,'hp_reference':hp,'capabilities':capabilities,'conventions':deepcopy(CONVENTIONS),'reference_cases':cases,
        'coverage_policy':'All menu/option review statuses are independent of related routes. Counts are inventory, never completion percentages.'}
    validate_catalog(result);return result

def validate_catalog(value):
    if not isinstance(value,dict) or value.get('format')!=FORMAT or value.get('schema_version')!=SCHEMA:raise ValueError('Formato de capacidades incompatible.')
    if value.get('platform') not in ('pc','hp'):raise ValueError('Plataforma desconocida.')
    if not isinstance(value.get('version'),str):raise ValueError('Versión faltante.')
    capabilities=value.get('capabilities');conventions=value.get('conventions')
    if not isinstance(capabilities,list) or not isinstance(conventions,dict):raise ValueError('Catálogo incompleto.')
    seen=set()
    for entry in capabilities:
        if not isinstance(entry,dict) or not isinstance(entry.get('id'),str) or not entry['id'] or entry['id'] in seen:raise ValueError('Identificadores de capacidad faltantes o duplicados.')
        seen.add(entry['id'])
        if not isinstance(entry.get('title'),str) or not isinstance(entry.get('status'),str):raise ValueError('Capacidad sin título o estado.')
        ids=entry.get('convention_ids',[])
        if not isinstance(ids,list) or any(not isinstance(key,str) or key not in conventions for key in ids):raise ValueError('Convención faltante.')
    case_ids=set()
    for case in value.get('reference_cases',[]):
        if not isinstance(case,dict) or not isinstance(case.get('id'),str) or case['id'] in case_ids:raise ValueError('Caso de referencia inválido o duplicado.')
        case_ids.add(case['id'])
        if case.get('capability_id') not in seen or case.get('convention_id') not in conventions:raise ValueError('Caso sin capacidad o convención conocida.')
    reference=value.get('hp_reference',{})
    if not isinstance(reference,dict):raise ValueError('Referencia HP inválida.')
    menus=reference.get('menus',[])
    if not isinstance(menus,list):raise ValueError('Menús HP inválidos.')
    menu_ids=set();option_ids=set()
    for menu in menus:
        if not isinstance(menu,dict) or not isinstance(menu.get('id'),str) or menu['id'] in menu_ids:raise ValueError('Identificador de menú inválido o duplicado.')
        menu_ids.add(menu['id'])
        if not isinstance(menu.get('options'),list):raise ValueError('Opciones de menú inválidas.')
        for option in menu['options']:
            if not isinstance(option,dict) or not isinstance(option.get('id'),str) or option['id'] in option_ids:raise ValueError('Identificador de opción inválido o duplicado.')
            option_ids.add(option['id'])
    for entry in capabilities:
        if any(key not in menu_ids for key in entry.get('hp_menu_ids',[])):raise ValueError('Referencia a menú HP inexistente.')
    json.dumps(value,allow_nan=False)
    return value

def load_catalog(path):
    return validate_catalog(json.loads(Path(path).read_text(encoding='utf-8-sig')))

def save_catalog(catalog,path):
    validate_catalog(catalog)
    Path(path).write_text(json.dumps(catalog,ensure_ascii=False,allow_nan=False,indent=2)+'\n',encoding='utf-8')

def compare_catalogs(before,after):
    """Comparación simétrica en datos, direccional en añadidos/retirados. Nunca aplica cambios."""
    validate_catalog(before);validate_catalog(after)
    def diff(left,right):
        return {'added':[right[key] for key in sorted(right.keys()-left.keys())],
            'removed':[left[key] for key in sorted(left.keys()-right.keys())],
            'changed':[{'id':key,'before':left[key],'after':right[key]} for key in sorted(left.keys()&right.keys()) if left[key]!=right[key]]}
    capabilities=diff({e['id']:e for e in before['capabilities']},{e['id']:e for e in after['capabilities']})
    conventions=diff(before['conventions'],after['conventions'])
    # Líneas son ubicaciones de evidencia, no identidades ni modificaciones funcionales.
    def menu_map(catalog):
        return {entry['id']:{key:value for key,value in entry.items() if key!='line'} for entry in catalog.get('hp_reference',{}).get('menus',[])}
    menus=diff(menu_map(before),menu_map(after))
    cases=diff({e['id']:e for e in before.get('reference_cases',[])},{e['id']:e for e in after.get('reference_cases',[])})
    return {'format':'signallab-capability-diff','schema_version':1,'before':{'platform':before['platform'],'version':before['version']},'after':{'platform':after['platform'],'version':after['version']},
        'capabilities':capabilities,'conventions':conventions,'hp_menus':menus,'reference_cases':cases,'requires_review':before.get('hp_reference',{}).get('sha256')!=after.get('hp_reference',{}).get('sha256') or any(group[key] for group in (capabilities,conventions,menus,cases) for key in ('added','removed','changed')),
        'source_hash_changed':before.get('hp_reference',{}).get('sha256')!=after.get('hp_reference',{}).get('sha256'),
        'policy':'Informe para revisión humana. No sincroniza código, no promueve estados de cobertura y no ejecuta contenido.'}

def check_reference(path,catalog):
    expected=catalog.get('hp_reference',{}).get('sha256')
    if not expected:raise ValueError('Catálogo sin hash de referencia HP.')
    actual=hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()
    return {'matches':actual==expected.upper(),'expected_sha256':expected,'actual_sha256':actual,'path':str(Path(path).resolve())}

def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description='Vinculación de capacidades SignalLab HP ↔ PC, sin sincronización de código.')
    sub=parser.add_subparsers(dest='command',required=True)
    export=sub.add_parser('export');export.add_argument('--hp-source',required=True);export.add_argument('--output',required=True)
    compare=sub.add_parser('compare');compare.add_argument('before');compare.add_argument('after');compare.add_argument('--output',required=True)
    check=sub.add_parser('check-reference');check.add_argument('catalog');check.add_argument('source')
    args=parser.parse_args(argv)
    if args.command=='export':
        catalog=build_catalog(Path(args.hp_source).read_bytes());save_catalog(catalog,args.output)
        print(json.dumps({'pc_tools':len(catalog['capabilities']),**catalog['hp_reference']['counts']}));return 0
    if args.command=='compare':
        result=compare_catalogs(load_catalog(args.before),load_catalog(args.after));Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('Comparación guardada; requiere revisión: '+str(result['requires_review']));return 0
    result=check_reference(args.source,load_catalog(args.catalog));print(json.dumps(result,ensure_ascii=False));return 0 if result['matches'] else 2

if __name__=='__main__':raise SystemExit(main())
