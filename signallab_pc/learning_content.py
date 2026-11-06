"""Conceptos antes de procedimientos: lectura guiada según los programas de 2026."""
from .library_content import read_data
GLOSSARY=read_data('glossary.json','terms')
if not isinstance(GLOSSARY,dict) or any(not isinstance(k,str) or not isinstance(v,str) or not k or not v for k,v in GLOSSARY.items()):raise ValueError('El glosario requiere términos y definiciones no vacíos.')

from .library_concepts import TOPICS


def concept_sections():
    topics=[dict(title=t,category='Conceptos · '+course,route=None,purpose=intro,usage=example,blocks=[('Idea principal',intro),('Relación matemática',formula),('Cómo interpretarlo',example),('Condiciones y alcance',limit)]) for t,course,intro,formula,example,limit in TOPICS]
    topics.insert(0,dict(title='Glosario: siglas y palabras frecuentes',category='Conceptos · Primeros pasos',route=None,purpose='Definiciones breves para leer fórmulas e informes.',usage=' '.join(GLOSSARY),blocks=[(term,meaning) for term,meaning in GLOSSARY.items()]))
    return topics

def concept_for(section):
    kind=section['route'][1];category=section.get('legacy_category',section['category'])
    if kind=='dsp_extensions':
        return [('Alcance','Estas herramientas trabajan con registros finitos. Hilbert usa extensión periódica; STFT analiza ventanas; la convolución por bloques usa extensión por ceros. Las condiciones de borde son parte del modelo.')]
    index=13 if kind=='state_space' else 1 if kind=='expression_measures' or section['route'][2]=='measures' else 4 if kind=='frequency_filter' else 7 if category=='Transformadas' else 6 if category=='Muestreo' else 10 if 'correlation' in kind else 9 if category=='Señales aleatorias' else 3 if category=='Fourier' else 8 if category=='Filtros y sistemas' else 2 if category in ('Control','Operaciones') else 0
    t,course,intro,formula,example,limit=TOPICS[index]
    return [('Concepto: '+t,intro),('Relación matemática',formula),('Ejemplo de interpretación',example),('Alcance del modelo',limit)]
