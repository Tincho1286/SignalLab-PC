"""One mathematical presentation for worksheet cells and saved results."""
import html
from .theme_tokens import COLORS as C
from .vector_math import render_latex

def math_formula(latex,size=17):
    if len(latex)>1600:raise ValueError('Vista matemática extensa')
    return render_latex(latex,size=size,color=C['text'])

def presentation_html(view,value,width,size=17):
    def present(value,width):
        kind=value['kind']
        if kind=='scalar':
            text=value.get('text','')
            if 'piecewise' in text.lower():
                structured=view._render_formula(text,math_size=size)
                if structured:return structured
            try:
                formula=math_formula(value['latex'],size)
                note='<p style="color:'+C['muted']+'">Fórmula extensa · desplazamiento horizontal disponible; Ampliar resultado abre una vista aparte.</p>' if formula.width>width else ''
                return note+'<p>'+view.vector_math_html(formula,value.get('text',''))+'</p>'
            except Exception:return '<pre style="font-family:Consolas">'+html.escape(value.get('pretty',value['text']))+'</pre>'
        if kind=='matrix':
            columns=min(value['columns'],8,max(1,int((width-60)//70)));cell_width=max(18,(width-40)/max(1,columns)-12)
            rows=''.join('<tr>'+''.join('<td align="center" style="padding:3px 6px">'+present(cell,cell_width)+'</td>' for cell in row[:columns])+'</tr>' for row in value['cells'])
            partial='<p>Vista parcial · matriz completa en Hoja → Texto completo y en Copiar resultado.</p>' if value['rows']>12 or value['columns']>columns else ''
            return '<table><tr><td style="font-size:28pt">[</td><td><table>'+rows+'</table></td><td style="font-size:28pt">]</td></tr></table>'+partial
        if kind=='mapping':return '<table>'+''.join('<tr><td>'+present(k,width*.35)+'</td><td>→</td><td>'+present(v,width*.55)+'</td></tr>' for k,v in value['items'])+'</table>'
        body=''.join(present(item,width-16) for item in value['items'])
        return '<p>Lista · '+str(value['total'])+' elementos</p>'+body+('<p>Vista parcial; texto completo disponible al exportar.</p>' if value['total']>20 else '')
    return present(value,width)
