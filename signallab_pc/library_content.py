"""Validated educational content, separate from the visual library and routing."""
from pathlib import Path
from functools import lru_cache
import json


def data_root():return Path(__file__).parent/'assets/library'


def read_content(root=None):
    root=data_root() if root is None else Path(root)
    shared=json.loads((root/'fragments.json').read_text(encoding='utf-8'))
    if shared.get('version')!=1:raise ValueError('Versión de fragmentos de la biblioteca no compatible.')
    def text(value):
        if isinstance(value,str) and value.strip():return value
        if isinstance(value,dict) and set(value)=={'ref'} and value['ref'] in shared['texts']:
            result=shared['texts'][value['ref']]
            if isinstance(result,str) and result.strip():return result
        raise ValueError('Texto vacío o referencia inexistente en la biblioteca.')
    def pairs(value):
        if not isinstance(value,list) or not value:raise ValueError('La biblioteca requiere bloques o parámetros no vacíos.')
        result=[]
        for row in value:
            if not isinstance(row,list) or len(row)!=2 or not isinstance(row[0],str) or not row[0].strip():raise ValueError('Cada bloque requiere título y texto.')
            result.append((row[0],text(row[1])))
        return result
    def key(row):
        value=row.get('key')
        if not isinstance(value,list) or len(value)!=2 or not isinstance(value[0],str) or type(value[1]) not in (str,int):raise ValueError('Ruta de biblioteca no válida.')
        return tuple(value)
    articles={};guides={};paths=sorted((root/'topics').glob('*.json'))
    if not paths:raise ValueError('No se encontraron los temas de la biblioteca.')
    for path in paths:
        document=json.loads(path.read_text(encoding='utf-8'))
        if document.get('version')!=1 or not isinstance(document.get('category'),str):raise ValueError('Tema de biblioteca no compatible: '+path.name)
        for row in document.get('articles',[]):
            route=key(row)
            if route in articles:raise ValueError('Artículo duplicado: '+str(route))
            articles[route]=pairs(row['blocks'])
        for row in document.get('guides',[]):
            route=key(row)
            if route in guides:raise ValueError('Guía duplicada: '+str(route))
            flow=row['flow']
            if not isinstance(flow,list) or len(flow)!=3 or any(not isinstance(v,str) or not v for v in flow):raise ValueError('Cada recorrido requiere entrada, operación y salida.')
            guides[route]=dict(flow=tuple(flow),parameters=pairs(row['parameters']),reading=text(row['reading']))
    def legacy(value):
        if isinstance(value,dict) and set(value)=={'tuple'}:return tuple(legacy(v) for v in value['tuple'])
        if isinstance(value,dict):return {k:legacy(v) for k,v in value.items()}
        if isinstance(value,list):return [legacy(v) for v in value]
        return value
    return articles,guides,legacy(shared['legacy_constants'])


@lru_cache(maxsize=1)
def default_content():return read_content()


@lru_cache(maxsize=None)
def read_data(filename,field):
    if filename not in {'concepts.json','functions.json','cas.json','glossary.json','relations.json'}:raise ValueError('Documento de biblioteca no reconocido.')
    document=json.loads((data_root()/filename).read_text(encoding='utf-8'))
    if document.get('version')!=1 or field not in document:raise ValueError('Documento de biblioteca incompatible: '+filename)
    return document[field]


def block_pairs(blocks):
    if not isinstance(blocks,list) or not blocks:raise ValueError('Un artículo debe tener contenido.')
    result=[]
    for row in blocks:
        if not isinstance(row,list) or len(row)!=2 or any(not isinstance(value,str) or not value.strip() for value in row):raise ValueError('Cada bloque requiere un título y un texto no vacíos.')
        result.append(tuple(row))
    return result
