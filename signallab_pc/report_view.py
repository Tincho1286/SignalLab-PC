from .atomic_file import write_text
"""Informes de lectura: presentación HTML local con texto original exportable."""
import ast
import html
import json
import re
from PySide6.QtWidgets import QTextBrowser,QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QFileDialog,QMessageBox,QApplication
from PySide6.QtCore import QUrl,Qt,QByteArray,QBuffer,QIODevice
from PySide6.QtGui import QTextDocument,QImage,QPainter,QColor
from .math_display import formula_vector
from .vector_math import MathImageHandler
from .expression_structure import parse_cases
from .signal_notation import normalize_source

from .theme_tokens import COLORS as C,colorize

PAPER_CSS=colorize("""
body {font-family:Cambria;font-size:11pt;color:@text@;background-color:@report@;}
h1 {font-family:'Segoe UI';font-size:15pt;font-weight:600;color:@text@;margin:0 0 14px;}
h2 {font-family:'Segoe UI';font-size:11pt;font-weight:600;color:@accent@;margin:16px 0 8px;}
h3 {font-family:'Segoe UI';font-size:10pt;font-weight:600;color:@accent@;}
p {line-height:145%;} td {vertical-align:top;} a {color:@accent@;}
""")
PAPER_COLORS={'#dce4ef': '#e1e7ee', '#e2eaf5': '#e1e7ee', '#e1e2e5': '#e1e7ee', '#27313b': '#e1e7ee', '#95a9bf': '#a6b2c1', '#aebccd': '#a6b2c1', '#8194ae': '#a6b2c1', '#91a0b5': '#a6b2c1', '#586b7a': '#a6b2c1', '#617382': '#a6b2c1', '#10151e': '#1b2027', '#151e2b': '#1b2027', '#131d2a': '#1b2027', '#ffffff': '#1b2027', '#293646': '#3c4653', '#2a384a': '#3c4653', '#d7dfe5': '#3c4653', '#294d68': '#8ab6df', '#3b5368': '#a6b2c1', '#235d87': '#8ab6df', '#53cbb6': '#79c4ad', '#087c68': '#79c4ad'}

_paper_tokens={'#e1e7ee':C['text'],'#a6b2c1':C['muted'],'#1b2027':C['report'],'#3c4653':C['border'],'#8ab6df':C['accent'],'#79c4ad':C['green']}
PAPER_COLORS={old:_paper_tokens.get(mapped,mapped) for old,mapped in PAPER_COLORS.items()}

def paper_html(text):
    from .theme_presets import color,recolor
    css=recolor(PAPER_CSS)
    def declaration(match):
        value=re.sub(r'#[0-9a-fA-F]{6}',lambda match:color(PAPER_COLORS.get(match.group().lower(),match.group())),match[2])
        return match[1]+':'+value
    text=re.sub(r'(color|background(?:-color)?|border(?:-[a-z]+)?):([^;"<>]+)',declaration,str(text))
    text=text.replace('font-family:Segoe UI','font-family:Cambria')
    if '<head>' in text:return text.replace('<head>','<head><style>'+css+'</style>',1)
    if '<html>' in text:return text.replace('<html>','<html><head><style>'+css+'</style></head>',1)
    return '<html><head><style>'+css+'</style></head><body>'+text+'</body></html>'

LABELS={'average_power':'Potencia media del registro','sample_count':'Cantidad de muestras','interpretation':'Interpretación','input_origins':'Orígenes de entrada','input_origin':'Origen de entrada','output_variable':'Variable de salida','scope':'Alcance','roc':'Región de convergencia','parameters':'Parámetros','evaluated':'Cálculo evaluado','realization':'Realización','operation':'Operación','sample_rate_hz':'Frecuencia de muestreo (Hz)','time_start_s':'Tiempo inicial (s)','input_length':'Muestras de entrada','output_length':'Muestras de salida','convention':'Convención','method':'Método','domain':'Dominio','origin':'Origen','step':'Paso','units':'Unidades','energy':'Energía','power':'Potencia','rms':'RMS','N':'Cantidad de puntos','count':'Cantidad de puntos','metadata':'Detalles','input_action':'Tratamiento de la entrada','period':'Periodo','normalization':'Normalización','time_mapping':'Relación entre índice y tiempo'}
LABELS['sample_period_s']='Período de muestreo T (s)'

def label(key):return LABELS.get(key,str(key).replace('_',' ').strip().capitalize())
def value_html(value,render=None):
    if isinstance(value,dict):return table_html(value,render)
    if isinstance(value,(list,tuple)):
        return '<span>'+html.escape(', '.join(str(v) for v in value))+'</span>'
    if isinstance(value,bool):return 'Sí' if value else 'No'
    if value is None:return 'No disponible'
    translations={'sampling':'Muestreo de una expresión','discrete':'Secuencia discreta','continuous':'Tiempo continuo','frequency':'Espectro','digital':'Digital','analog':'Analógico','True':'Verdadera','False':'Falsa','t = time_start_s + (n-origin)/sample_rate_hz':'t = t₀ + (n − n₀) / Fs'}
    if render and isinstance(value,str) and (any(c in value for c in ('**','^','/','(', 'sqrt','<','>','=')) or re.fullmatch(r'[+-]?[0-9]+(?:\.[0-9]*)?[eE][+-]?[0-9]+',value.strip())):
        shown=render(value.strip())
        if shown:return shown
    return html.escape(translations.get(str(value),str(value))).replace('\n','<br>')
def table_html(data,render=None):
    entries=data.items() if isinstance(data,dict) else data
    return '<table width="100%" cellspacing="0" cellpadding="9">'+''.join('<tr><td width="38%" valign="top" style="color:#95a9bf;border-bottom:1px solid #293646">'+html.escape(label(k))+'</td><td style="color:#e2eaf5;border-bottom:1px solid #293646">'+value_html(v,render)+'</td></tr>' for k,v in entries)+'</table>'
def report_html(text,render=None,body_only=False):
    parts=[];cursor=0
    # Sólo objetos JSON completos: el resto siempre se escapa como texto.
    decoder=json.JSONDecoder()
    while cursor<len(text):
        start=text.find('{',cursor)
        if start<0:parts.append(('text',text[cursor:]));break
        try:obj,end=decoder.raw_decode(text[start:])
        except ValueError:parts.append(('text',text[cursor:start+1]));cursor=start+1;continue
        parts.append(('text',text[cursor:start]));parts.append(('json',obj));cursor=start+end
    body=[]
    for kind,data in parts:
        if kind=='json':body.append(table_html(data,render));continue
        for paragraph in re.split(r'\n\s*\n',data.strip()):
            if not paragraph:continue
            lines=paragraph.splitlines()
            if all(':' in line and len(line.split(':',1)[0])<65 for line in lines):
                body.append(table_html([line.split(':',1) for line in lines],render))
            elif render and len(lines)==1 and any(c in paragraph for c in ('**','^','/','(')) and (formula:=render(paragraph.strip())):body.append('<p>'+formula+'</p>')
            else:
                presented=[(render(line.strip()) if render and any(c in line for c in ('=','/','^','(')) else None) or html.escape(line) for line in lines]
                body.append('<p style="line-height:150%;margin:0 0 16px">'+'<br>'.join(presented)+'</p>')
    if body_only:return ''.join(body)
    return '<html><body style="font-family:Segoe UI;font-size:11pt;color:#dce4ef;margin:18px">'+''.join(body)+'</body></html>'
class ReportView(QTextBrowser):
    def __init__(self,parent=None):
        super().__init__(parent);self._calculation_notes=[];self._base_html='';self._report_revision=0;self._raw='';self.setOpenExternalLinks(False);self.setOpenLinks(False);self.setObjectName('resultReport')
        self._math_resources={};self._formula_number=0;self._math_handler=MathImageHandler(self.document(),self._math_resources)
    def setHtml(self,text):
        self._base_html=str(text);self._report_revision+=1
        if self._calculation_notes:
            from .calculation_notes import callout_html
            from .vector_math import render_latex
            def render(value):return self.vector_math_html(render_latex(value,size=15))
            callout=callout_html(self._calculation_notes,render)
            text=re.sub(r'(<body[^>]*>)',lambda match:match.group(1)+callout,str(text),count=1,flags=re.I) if re.search(r'<body[^>]*>',str(text),re.I) else callout+str(text)
        super().setHtml(paper_html(text))
        self._math_handler.prune({html.unescape(value) for value in re.findall(r'src="([^"]+)"',str(text))})
    def refresh_theme(self,previous):
        from dataclasses import replace
        from .theme_presets import recolor
        revision=self._report_revision;vertical=self.verticalScrollBar().value();horizontal=self.horizontalScrollBar().value()
        for name,formula in list(self._math_resources.items()):
            value=replace(formula,svg=recolor(formula.svg.decode('utf-8'),previous).encode('utf-8'))
            self._math_resources[name]=value;self.document().addResource(QTextDocument.ResourceType.ImageResource,QUrl(name),QByteArray(value.svg))
        self._math_handler.renderers.clear();self.setHtml(self._base_html);self._report_revision=revision
        self.verticalScrollBar().setValue(vertical);self.horizontalScrollBar().setValue(horizontal);self.viewport().update()
    def set_calculation_notes(self,records):
        self._calculation_notes=[dict(record) for record in records]
        self.setHtml(self._base_html)
    def vector_math_html(self,formula,source='',width=None):
        from dataclasses import replace
        from .theme_presets import recolor
        formula=replace(formula,svg=recolor(formula.svg.decode('utf-8')).encode('utf-8'))
        self._formula_number+=1;name='formula:'+str(self._formula_number)
        self._math_resources[name]=formula
        self.document().addResource(QTextDocument.ResourceType.ImageResource,QUrl(name),QByteArray(formula.svg))
        width=formula.width if width is None else width;height=formula.height*width/formula.width
        return '<img src="'+name+'" width="'+str(max(1,round(width)))+'" height="'+str(max(1,round(height)))+'" alt="'+html.escape(source,quote=True)+'">'
    def setPlainText(self,text):
        self._raw=str(text);self._formula_number=0;self.setHtml(report_html(self._raw,self._render_formula))
    def set_readable(self,summary):
        self._formula_number=0;self._raw=summary.plain_text();parts=['<h1>'+html.escape(summary.title)+'</h1>']
        for section in summary.sections:
            if section.title:parts.append('<h2>'+html.escape(section.title)+'</h2>')
            for paragraph in section.paragraphs:parts.append('<p style="line-height:150%">'+html.escape(str(paragraph))+'</p>')
            if section.rows:
                parts.append('<table width="100%" cellspacing="0" cellpadding="7">'+''.join('<tr><td valign="top" width="45%" style="color:#aebccd">'+html.escape(str(key))+'</td><td>'+value_html(value,self._render_formula)+'</td></tr>' for key,value in section.rows)+'</table>')
            for formula in section.formulas:
                render=lambda value:self._render_formula(value,numeric=formula.numeric)
                if formula.lines:
                    for index,line in enumerate(formula.lines):parts.append('<p style="margin-left:'+str(28 if index else 0)+'px">'+(render(line) or html.escape(line))+'</p>')
                else:parts.append('<p>'+(render(formula.expression) or html.escape(formula.text))+'</p>')
        self.setHtml('<html><body style="font-family:Segoe UI;font-size:11pt;color:#dce4ef;margin:18px">'+''.join(parts)+'</body></html>')
    def set_matrices(self,summary,matrices):
        import numpy as np
        self._formula_number=0;body=[report_html(str(summary),self._render_formula,body_only=True)];raw=[str(summary)]
        def number(value):
            z=complex(value)
            if not z.imag:return format(z.real,'.12g')
            if not z.real:return format(z.imag,'.12g')+'i'
            return format(z.real,'.12g')+(' + ' if z.imag>=0 else ' − ')+format(abs(z.imag),'.12g')+'i'
        for title,value in matrices.items():
            array=np.asarray(value)
            if array.ndim!=2:raise ValueError('El informe de matrices requiere dos dimensiones.')
            rows,columns=array.shape;shown=array[:20,:12]
            raw.append(str(title)+' =\n'+np.array2string(array))
            body.append('<h3>'+html.escape(str(title))+f' · {rows} × {columns}</h3>')
            if not rows or not columns:body.append('<p>Matriz vacía.</p>');continue
            def bracket(right=False):
                height=max(30,len(shown)*32);image=QImage(10,height,QImage.Format.Format_ARGB32_Premultiplied);image.fill(Qt.GlobalColor.transparent)
                painter=QPainter(image);painter.setPen(QColor(C['muted']));x,edge=(8,1) if right else (1,8)
                painter.drawLine(x,1,x,height-2);painter.drawLine(x,1,edge,1);painter.drawLine(x,height-2,edge,height-2);painter.end()
                self._formula_number+=1;url=QUrl('matrix-bracket:'+str(self._formula_number));self.document().addResource(QTextDocument.ResourceType.ImageResource,url,image)
                return '<td rowspan="'+str(len(shown))+'"><img src="'+url.toString()+'" width="10" height="'+str(height)+'"></td>'
            left_bracket,right_bracket=bracket(),bracket(True);cells=''
            for index,row in enumerate(shown):
                cells+='<tr>'+(left_bracket if index==0 else '')+''.join('<td align="right" style="padding:6px 12px">'+html.escape(number(z))+'</td>' for z in row)+(right_bracket if index==0 else '')+'</tr>'
            body.append('<table cellspacing="0">'+cells+'</table>')
            if rows>20 or columns>12:body.append('<p>Vista parcial: primeras 20 filas y 12 columnas como máximo. La matriz completa se conserva en el modelo disponible en Resultados anteriores.</p>')
        body.append('<p style="color:#95a9bf">Presentación con hasta 12 cifras significativas. El modelo conserva la precisión numérica de sus coeficientes.</p>')
        self._raw='\n\n'.join(raw)
        self.setHtml('<html><body style="font-family:Segoe UI;font-size:11pt;color:#dce4ef;margin:18px">'+''.join(body)+'</body></html>')
    def _render_formula(self,source,numeric=False,leading_dot=False):
        try:
            # Numerical output is already normalized. Re-reading its decimals
            # as exact rationals would create huge fractions in every mode.
            render=lambda value:self._render_formula(value,numeric=numeric)
            if len(source)>1000:return None
            equation=re.fullmatch(r'([A-Za-z]\w*(?:(?:\([^=]*\))|(?:\[[^=]*\]))?)\s*=\s*(.+)',source.strip())
            if equation:
                discrete=bool(re.search(r'\[\s*[nk]\s*\]',equation[1]))
                left=render(equation[1]);right=render(equation[2] if numeric else normalize_source(equation[2],discrete))
                if left and right:return left+' = '+right if numeric else '<table><tr><td>'+left+'</td><td> = </td><td>'+right+'</td></tr></table>'
                return None
            if not numeric:source=normalize_source(source)
            cases=parse_cases(source)
            rows=[]
            if cases:
                rows,otherwise=cases
                if otherwise is not None:rows=[*rows,(otherwise,'True')]
            if rows:
                undefined='<p>Fuera de estos casos no hay un valor definido.</p>' if not any(condition=='True' for _,condition in rows) else ''
                body=''.join('<tr><td style="padding:8px">'+(render(value) or html.escape(value))+'</td><td style="padding:8px">'+('en los demás casos' if condition=='True' else 'si '+(render(condition) or html.escape(condition)))+'</td></tr>' for value,condition in rows)
                return '<table><tr><td style="font-size:36pt">{</td><td><table>'+body+'</table></td></tr></table><p style="color:#95a9bf;font-size:9pt">Tramos en orden: se usa la primera condición que se cumple.</p>'+undefined
            if 'Piecewise' in source:
                # Preserve arbitrary supports: show a short expression and the
                # actual cases as definitions instead of leaking Python syntax.
                tree=ast.parse(source,mode='eval');definitions=[]
                occupied={v.id for v in ast.walk(tree) if isinstance(v,ast.Name)}
                class Cases(ast.NodeTransformer):
                    def visit_Call(inner,node):
                        if isinstance(node.func,ast.Name) and node.func.id=='Piecewise':
                            index=len(definitions)+1;name='g'+str(index)
                            while name in occupied:index+=1;name='g'+str(index)
                            occupied.add(name)
                            variables=sorted({v.id for v in ast.walk(node) if isinstance(v,ast.Name) and v.id in ('t','n','k','w','tau')})
                            alias=ast.Call(func=ast.Name(id=name,ctx=ast.Load()),args=[ast.Name(id=v,ctx=ast.Load()) for v in variables],keywords=[]) if variables else ast.Name(id=name,ctx=ast.Load())
                            definitions.append((ast.unparse(alias),ast.unparse(node)))
                            return ast.copy_location(alias,node)
                        return inner.generic_visit(node)
                tree=Cases().visit(tree);main=render(ast.unparse(tree))
                if main and definitions:
                    body=[main]
                    for name,value in definitions:
                        shown=render(value)
                        if not shown:return None
                        body.append('<table><tr><td>'+render(name)+'</td><td> = </td><td>'+shown+'</td></tr></table>')
                    return '<br>'.join(body)
            if numeric:
                from .math_display import numeric_presentation
                source=numeric_presentation(source)
                tree=ast.parse(source,mode='eval').body;positive=isinstance(tree,ast.UnaryOp) and isinstance(tree.op,ast.UAdd)
                if positive:tree=tree.operand
                def factors(node):
                    if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Mult):return factors(node.left)+factors(node.right)
                    return [node]
                terms=factors(tree)
                if len(terms)>1:
                    fragments=[]
                    for index,term in enumerate(terms):
                        text=ast.unparse(term)
                        if isinstance(term,ast.BinOp) and isinstance(term.op,(ast.Add,ast.Sub)):text='('+text+')'
                        if positive and index==0:text='+'+text
                        fragment=self._render_formula(text,numeric=True,leading_dot=index>0)
                        if not fragment:return None
                        fragments.append(fragment)
                    # Separate factors may wrap; the dot belongs to its factor,
                    # so a continued product cannot be mistaken for a new sum.
                    return ' '.join(fragments)
            return self.vector_math_html(formula_vector(source,leading_dot),source)
        except Exception:return None
    def appendPlainText(self,text):self.setPlainText(self._raw+'\n\n'+str(text))
    def toPlainText(self):
        from .calculation_notes import plain_text
        notes=plain_text(self._calculation_notes)
        return self._raw+('\n\n'+notes if notes else '')
    def clear(self):self.setPlainText('')

    def export_document(self,formatted=True):
        from pathlib import Path
        suffix='html' if formatted else 'txt'
        path,_=QFileDialog.getSaveFileName(self,'Exportar informe','informe.'+suffix,'Documento HTML (*.html)' if formatted else 'Texto (*.txt)')
        if not path:return
        if not Path(path).suffix:path+='.'+suffix
        try:
            text=self.toPlainText()
            if formatted:
                # Incrustar las imágenes para que el informe sea un único archivo portable.
                def embed(match):
                    url=html.unescape(match.group(1))
                    if url in self._math_resources:
                        import base64
                        return 'src="data:image/svg+xml;base64,'+base64.b64encode(self._math_resources[url].svg).decode('ascii')+'"'
                    resource=self.document().resource(QTextDocument.ResourceType.ImageResource,QUrl(url))
                    if not isinstance(resource,QImage) or resource.isNull():return match.group(0)
                    data=QByteArray();buffer=QBuffer(data);buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                    if not resource.save(buffer,'PNG'):raise ValueError('No se pudo incluir una fórmula en el informe.')
                    buffer.close()
                    return 'src="data:image/png;base64,'+bytes(data.toBase64()).decode('ascii')+'"'
                text=re.sub(r'src="([^"]+)"',embed,self.toHtml())
                text=text.replace('</head>','<meta charset="utf-8"><style>body { background:#1b2027; color:#e1e7ee; padding:24px; max-width:1100px; margin:auto; } img { max-width:100%; height:auto; }</style></head>')
            write_text(path,text)
        except Exception as exc:QMessageBox.warning(self,'No se pudo exportar el informe',str(exc))

def report_panel(report):
    """Acciones visibles sobre el informe, sin modificar su contenido original."""
    panel=QWidget();layout=QVBoxLayout(panel);layout.setContentsMargins(0,0,0,0)
    bar=QHBoxLayout()
    copy=QPushButton('Copiar texto');copy.clicked.connect(lambda:QApplication.clipboard().setText(report.toPlainText()));bar.addWidget(copy)
    save=QPushButton('Guardar informe con formato…');save.clicked.connect(lambda:report.export_document(True));bar.addWidget(save)
    plain=QPushButton('Guardar texto…');plain.clicked.connect(lambda:report.export_document(False));bar.addWidget(plain)
    bar.addStretch();layout.addLayout(bar);layout.addWidget(report,1)
    return panel
