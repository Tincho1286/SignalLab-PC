"""Convergence hints shared by expression/system reuse actions."""
from copy import deepcopy


def result_roc(value):
    if not isinstance(value,dict):return None
    request=value.get('request',{});result=value.get('result',{})
    if request.get('domain')=='digital' and 'roc_spec' in request:return deepcopy(request['roc_spec'])
    hint=result.get('inverse_roc_hint')
    if hint in ('right','left'):return {'mode':hint}
    if request.get('operation')=='z_finite' or 'roc_finite_plane' in result:return {'mode':'right'}
    return None
