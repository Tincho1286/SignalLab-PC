"""Compatibility API for authored library articles stored as thematic data."""
from .library_content import default_content
ARTICLES=default_content()[0]


def add(keys,purpose,load,result,conditions):
    if isinstance(keys[0],str):keys=[keys]
    for key in keys:ARTICLES[key]=[('Qué podés hacer',purpose),('Cómo preparar el cálculo',load),('Cómo interpretar la salida',result),('Qué tener en cuenta',conditions)]


def article_blocks(route):
    # Missing authorship is an error during development, not generic prose in UI.
    blocks=list(ARTICLES[tuple(route[1:3])])
    from .tool_catalog import locate
    entry=locate(route)
    if entry and len(entry['variants'])>1:blocks.insert(2,('Cambiar de vista','Cada variante conserva su entrada y su último resultado. La primera vez puede prepararse una copia compatible de la vista anterior. Al volver, tus datos se conservan; el enlace Copiar entrada permite reemplazarlos cuando lo elegís. Copiar datos no recalcula ni modifica una salida ya obtenida.'))
    blocks.append(('Biblioteca de resultados','Al calcular, la salida queda registrada en Resultados junto con su herramienta de origen. Allí podés consultarla, exportarla o usarla en un destino compatible. Una expresión se conserva como fórmula con sus condiciones: no necesitás convertirla primero en una función de transferencia. Las muestras, los sistemas y los modelos de estados conservan sus propios tipos.'))
    return blocks
