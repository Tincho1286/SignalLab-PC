"""Compatibility API for tool field references stored alongside library articles."""
from .library_content import default_content
_content=default_content()
GUIDES=_content[1]
SEQUENCE,TRANSFER,MATRICES,GROUPS=(_content[2][name] for name in ('SEQUENCE','TRANSFER','MATRICES','GROUPS'))


def add(kind,task,flow,parameters,reading):
    GUIDES[kind,task]={'flow':tuple(flow.split('|')),'parameters':[tuple(row.split(': ',1)) for row in parameters.split('\n') if row],'reading':reading}
