"""Readable library rendering for saved CAS values."""
import html
from .cas_presentation import presentation_html

def show_cas_result(view,value):
    answer=value['cas_answer'];view._formula_number=0
    body='<h1>Resultado CAS</h1><h2>Entrada</h2><p>'+html.escape(value.get('source',''))+'</p><h2>Resultado</h2>'
    body+=presentation_html(view,answer['presentation'],max(240,view.viewport().width()-60))
    if answer.get('assumptions'):
        body+='<h2>Supuestos del resultado</h2><table>'+''.join('<tr><td>'+html.escape(str(name))+'</td><td>'+html.escape(str(description))+'</td></tr>' for name,description in answer['assumptions'])+'</table>'
    body+=''.join('<p>'+html.escape(str(note))+'</p>' for note in answer.get('notices',[]))
    view.setHtml(body);view._raw=value.get('source','')+'\n\n'+answer['text']+'\n\n'+'\n'.join(answer.get('notices',[]))+'\n'+'\n'.join(str(name)+': '+str(description) for name,description in answer.get('assumptions',[]))
