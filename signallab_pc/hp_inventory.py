"""Inventario léxico HP PPL. Describe llamadas; nunca ejecuta código HP."""
from dataclasses import dataclass
import hashlib
import re
import unicodedata

@dataclass(frozen=True)
class Token:
    text: str
    kind: str
    start: int
    end: int

_PATTERN=re.compile(r'(?P<space>\s+)|(?P<comment>//[^\n]*|/\*.*?\*/)|(?P<string>"(?:\\.|[^"\\])*")|(?P<name>[A-Za-z_]\w*)|(?P<symbol>.)',re.S)
_PAIRS={'(':')','{':'}','[':']'}

def tokens(source):
    result=[]
    for match in _PATTERN.finditer(source):
        if match.lastgroup in ('space','comment'):continue
        if match.group()=='/' and source[match.start():match.start()+2]=='/*':raise ValueError('Comentario HP sin cierre.')
        if match.group()=='"':raise ValueError('Cadena HP sin cierre; no se generó un inventario parcial.')
        result.append(Token(match.group(),match.lastgroup,match.start(),match.end()))
    return result

def slug(text):
    normalized=''.join(c for c in unicodedata.normalize('NFKD',text.casefold()) if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+','-',normalized).strip('-') or 'dynamic'

def literal(part):
    if len(part)!=1 or part[0].kind!='string':return None
    return re.sub(r'\\(.)',lambda m:{'n':'\n','r':'\r','t':'\t'}.get(m[1],m[1]),part[0].text[1:-1])

def split_arguments(items,begin):
    """Divide sólo comas del nivel exterior; retorna argumentos e índice de cierre."""
    opener=items[begin].text
    if opener not in _PAIRS:raise ValueError('Se esperaba un delimitador de apertura.')
    stack=[_PAIRS[opener]];parts=[];start=begin+1
    for index in range(begin+1,len(items)):
        item=items[index]
        if item.kind=='string':continue
        if item.text in _PAIRS:stack.append(_PAIRS[item.text])
        elif item.text in (')','}',']'):
            if not stack or item.text!=stack[-1]:raise ValueError('Delimitadores HP incompatibles.')
            stack.pop()
            if not stack:
                if index>start:parts.append(items[start:index])
                elif parts:parts.append([])
                return parts,index
        elif item.text==',' and len(stack)==1:parts.append(items[start:index]);start=index+1
    raise ValueError('Llamada HP sin cierre; no se generó un inventario parcial.')

def extract_menus(source):
    items=tokens(source);menus=[];occurrences={}
    declarations=[]
    for index,item in enumerate(items[:-1]):
        if item.kind!='name' or items[index+1].text!='(':continue
        prefix=source[source.rfind('\n',0,item.start)+1:item.start]
        if not re.fullmatch(r'\s*(?:EXPORT\s+|VIEW\s+"[^"\n]*"\s*,\s*)?',prefix):continue
        _,end=split_arguments(items,index+1)
        if end+1<len(items) and items[end+1].text=='BEGIN':declarations.append((item.start,item.text))
    cursor=0;caller='GLOBAL'
    for index,item in enumerate(items[:-1]):
        if item.kind!='name' or item.text!='SSMenu' or items[index+1].text!='(':continue
        args,end=split_arguments(items,index+1)
        if end+1<len(items) and items[end+1].text=='BEGIN':continue
        while cursor<len(declarations) and declarations[cursor][0]<=item.start:
            caller=declarations[cursor][1];cursor+=1
        if len(args)<2:raise ValueError('SSMenu sin título u opciones.')
        title=literal(args[0]);base=f'hp.menu.{slug(caller)}.{slug(title or "dynamic")}'
        occurrences[base]=occurrences.get(base,0)+1;menu_id=f'{base}.{occurrences[base]}'
        expression=lambda part:source[part[0].start:part[-1].end] if part else ''
        options=[];option_parts=None
        if args[1] and args[1][0].text=='{':
            candidate,stop=split_arguments(args[1],0)
            if stop==len(args[1])-1:option_parts=candidate
        if option_parts is not None:
            for number,part in enumerate(option_parts,1):
                options.append({'id':f'{menu_id}.option.{number}','position':number,'label':literal(part),'expression':expression(part),'dynamic':literal(part) is None})
        menus.append({'id':menu_id,'caller':caller,'line':source.count('\n',0,item.start)+1,'title':title,'title_expression':expression(args[0]),'options_expression':expression(args[1]),'options':options,'dynamic_options':option_parts is None,'review_status':'unreviewed'})
    return menus

def source_inventory(data):
    source=data.decode('utf-8-sig')
    menus=extract_menus(source)
    return {'sha256':hashlib.sha256(data).hexdigest().upper(),'line_count':len(source.splitlines()),'menus':menus,
        'counts':{'menu_calls':len(menus),'literal_titles':sum(m['title'] is not None for m in menus),'dynamic_option_lists':sum(m['dynamic_options'] for m in menus),'explicit_options':sum(len(m['options']) for m in menus),'dynamic_option_expressions':sum(o['dynamic'] for m in menus for o in m['options'])},
        'scope':'SSMenu calls only; dashboard, conditional branches, theory, computed options and runtime behavior require separate review.'}
