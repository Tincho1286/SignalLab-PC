"""Compatibility API for authored library articles stored as thematic data."""
from .library_content import default_content
ARTICLES=default_content()[0]


def add(keys,purpose,load,result,conditions):
    if isinstance(keys[0],str):keys=[keys]
    for key in keys:ARTICLES[key]=[('Qué podés hacer',purpose),('Cómo preparar el cálculo',load),('Cómo interpretar la salida',result),('Qué tener en cuenta',conditions)]


def article_blocks(route):
    # Missing authorship is an error during development, not generic prose in UI.
    return list(ARTICLES[tuple(route[1:3])])
