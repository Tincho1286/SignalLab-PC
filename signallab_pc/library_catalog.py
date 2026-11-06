"""Single library catalog; educational data are independent of Qt rendering."""
from pathlib import Path
import json,re,unicodedata

CATEGORIES=('Fundamentos de señales','Señales continuas y discretas','Operaciones y transformaciones de señales','Sistemas LTI','Convolución y correlación','Series y transformadas de Fourier','Transformadas de Laplace y Z','Muestreo y reconstrucción','Análisis de sistemas','Diseño de filtros FIR e IIR','Ecuaciones diferenciales y en diferencias','Procesamiento digital de señales','Señales aleatorias','Herramientas matemáticas complementarias')

def data_root():
    return Path(__file__).parent/'assets/library'


def example_records():
    document=json.loads((data_root()/'examples.json').read_text(encoding='utf-8'))
    if document.get('version')!=1:raise ValueError('Versión de ejemplos no compatible.')
    examples=document['examples'];seen=set()
    from .workspaces import ROUTES
    for value in examples:
        for field in ('id','title','category','tool','statement','objective','request','procedure','expected','conditions','interpretation','variable'):
            if not value.get(field):raise ValueError('Falta '+field+' en el ejemplo.')
        if value['id'] in seen or not re.fullmatch('[a-z0-9-]+',value['id']):raise ValueError('Identificador de ejemplo inválido o repetido.')
        seen.add(value['id'])
        if value['category'] not in CATEGORIES or tuple(value['tool']) not in ROUTES:raise ValueError('Destino de ejemplo no disponible.')
    return examples


def category(section):
    route=section.get('route');kind=route[1] if route else '';task=route[2] if route else None
    if kind=='difference_equation' or kind=='symbolic' and task==4:return CATEGORIES[10]
    if kind in ('transform_lab','symbolic'):return CATEGORIES[6]
    if kind in ('random','random_correlation','random_model'):return CATEGORIES[12]
    if kind in ('sampling','rational_resampling'):return CATEGORIES[7]
    if kind in ('system_analysis','state_space'):return CATEGORIES[8]
    if kind in ('frequency_filter','fir_window') or kind=='systems' and task in (0,1,2,6,7):return CATEGORIES[9]
    if 'correlation' in kind or 'convolution' in kind or kind=='basic' and task in ('convolve','correlate','circular','continuous_convolution','continuous_correlation'):return CATEGORIES[4]
    if kind in ('fourier','fourier_symbolic','dtft_symbolic','inverse_dtft') or kind=='basic' and task in ('dft','idft'):return CATEGORIES[5]
    if kind=='dsp_extensions' or kind=='course_tools':return CATEGORIES[11]
    if kind in ('systems','interconnection'):return CATEGORIES[3]
    if kind in ('signal_product','time_transform'):return CATEGORIES[2]
    if kind in ('signal_editor','window_signal','basic'):return CATEGORIES[1]
    if section.get('reference') or kind=='cas':return CATEGORIES[13]
    title=section['title'].casefold()
    for word,index in [('aleator',12),('muestre',7),('alias',7),('fourier',5),('laplace',6),('convergencia',6),('lti',3),('filtro',9),('convol',4),('correl',4),('estado',8)]:
        if word in title:return CATEGORIES[index]
    return CATEGORIES[0]



def data_description(request):
    lines=['Expresión: '+request['expression']]
    if 'coefficients' in request:lines.append('Coeficientes a₀, a₁, …: '+', '.join(request['coefficients']))
    if 'initial' in request:lines.append(('Valores anteriores y[n₀−1], y[n₀−2], …: ' if request['operation']=='difference_equation' else 'Datos iniciales y(0−), y′(0−), …: ')+', '.join(request['initial']))
    if 'start' in request:lines.append('Índice inicial n₀: '+str(request['start']))
    if 'count' in request:lines.append('Muestras del gráfico: '+str(request['count']))
    if 'roc' in request:lines.append('ROC: interior a los polos.' if request['roc']=='left' else 'ROC: exterior a los polos.')
    if 'laplace_roc' in request:lines.append('Interpretación bilateral; ROC a la izquierda de los polos.')
    if request.get('domain')=='digital':lines.append('Variable z; interpretación y ROC indicadas en el enunciado.')
    return '\n'.join(lines)


def sections():
    from .cas_reference import cas_sections
    from .function_reference import function_sections
    from .learning_content import concept_sections
    from .help_content import sections as tools
    from .workspaces import ROUTES
    values=cas_sections()+function_sections()+concept_sections()+tools()
    for index,section in enumerate(values):
        route=section.get('route')
        section['article_id']='tool:'+str(route[1])+':'+str(route[2]) if route else 'reference:'+section['title']
        section['category']=category(section)
        section['content_kind']='reference' if section.get('reference') else 'tool' if route else 'concept'
    for example in example_records():
        route=ROUTES[tuple(example['tool'])]
        values.append(dict(title='Ejemplo: '+example['title'],article_id='example:'+example['id'],category=example['category'],route=route,content_kind='example',example=example,blocks=[('Enunciado',example['statement']),('Objetivo',example['objective']),('Datos',data_description(example['request'])),('Procedimiento verificado',example['procedure']),('Relación matemática',example['expected']),('Condiciones',example['conditions']),('Interpretación',example['interpretation'])]))
        for section in values:
            if section.get('content_kind')=='tool' and section.get('route')==route:section.setdefault('examples',[]).append((example['id'],example['title']))
    for section in values:
        section['purpose']=section.get('purpose') or section['blocks'][0][1]
        section['usage']=section.get('usage') or (section['blocks'][1][1] if len(section['blocks'])>1 else section['purpose'])
    order={'concept':0,'tool':1,'example':2,'reference':3}
    values.sort(key=lambda value:(CATEGORIES.index(value['category']),order[value['content_kind']],value['title']))
    return values
