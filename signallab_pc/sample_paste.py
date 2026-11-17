"""Explicit clipboard layouts with scalar expressions and uniform-axis validation."""
import math,re
import numpy as np
from .model import Signal
from .scalar_expression import integer_value,real_value
from .numeric_input import constant_value
from .resources import ensure_working_set

LAYOUTS={'values':'Una secuencia · fila o columna','axis_value':'Eje y valor','complex':'Parte real e imaginaria','axis_complex':'Eje, parte real e imaginaria'}


def _split(text,delimiter):
    fields=[];part=[];depth=0
    for char in text:
        if char in '([{':depth+=1
        elif char in ')]}':
            depth-=1
            if depth<0:raise ValueError('Hay un paréntesis o corchete sin abrir.')
        separator=char==delimiter if delimiter else char.isspace()
        if separator and depth==0:
            if part or delimiter:fields.append(''.join(part).strip());part=[]
        else:part.append(char)
    if depth:raise ValueError('Completá los paréntesis de cada expresión.')
    if part or delimiter:fields.append(''.join(part).strip())
    return fields


def rows(text,layout='values',decimal_comma=False,header=False):
    if layout not in LAYOUTS:raise ValueError('Elegí qué contiene cada columna.')
    ensure_working_set(len(text),bytes_per_sample=1,live_arrays=12)
    text=str(text).strip().lstrip('\ufeff').replace('\r\n','\n').replace('\r','\n')
    if text.startswith('[') and text.endswith(';'):text=text[:-1].rstrip()
    bracketed=text.startswith('[') and text.endswith(']')
    if bracketed:text=text[1:-1].strip().rstrip(';').strip().replace(';','\n')
    elif layout=='values' and '\n' not in text and not decimal_comma:text=text.replace(';','\n')
    lines=[line for line in text.splitlines() if line.strip()]
    if header:lines=lines[1:]
    parsed=[]
    for number,line in enumerate(lines,1):
        delimiter='\t' if '\t' in line else ';' if ';' in line else ',' if ',' in line and not decimal_comma else None
        fields=_split(line,delimiter)
        if delimiter is None and len(fields)>1 and len(fields)%2==1 and all(fields[i] in ('+','-','*','/','^','**') for i in range(1,len(fields),2)):fields=[line.strip()]
        if any(not cell for cell in fields):raise ValueError('Fila '+str(number)+': hay una celda vacía. No se reemplaza por cero.')
        parsed.append(fields)
    if not parsed:raise ValueError('Pegá al menos una muestra.')
    width=len(parsed[0])
    if any(len(row)!=width for row in parsed):raise ValueError('Todas las filas deben tener la misma cantidad de columnas.')
    if layout=='values':
        if len(parsed)>1 and width>1:raise ValueError('Esto es una tabla. Elegí Eje y valor o Parte real e imaginaria; no se mezclan sus columnas.')
        parsed=[[value] for row in parsed for value in row]
    else:
        expected=3 if layout=='axis_complex' else 2
        if width!=expected:raise ValueError('Esta disposición necesita exactamente '+str(expected)+' columnas.')
    if decimal_comma:
        def decimal(cell):
            if cell.count(',')>1 or ',' in cell and not re.fullmatch(r'[+-]?\d+,\d+(?:[eE][+-]?\d+)?',cell.strip()):raise ValueError('Coma decimal requiere un número decimal por celda; separá columnas con tabulación o punto y coma.')
            return cell.replace(',','.')
        parsed=[[decimal(cell) for cell in row] for row in parsed]
    ensure_working_set(len(parsed),bytes_per_sample=160,live_arrays=6)
    return parsed


def parse(text,kind='discrete',*,layout='values',origin='0',step='1',units=None,decimal_comma=False,header=False):
    if kind not in ('discrete','continuous','frequency'):raise ValueError('Elegí un dominio numérico admitido.')
    cells=rows(text,layout,decimal_comma,header);has_axis=layout.startswith('axis_');split_complex=layout in ('complex','axis_complex');axis=[];values=[]
    for i,row in enumerate(cells,1):
        try:
            start=1 if has_axis else 0
            if has_axis:axis.append(integer_value(row[0]) if kind=='discrete' else real_value(row[0]))
            if split_complex:
                real=constant_value(row[start]);imag=constant_value(row[start+1])
                if real.imag or imag.imag:raise ValueError('Las columnas Real e Imaginaria deben contener constantes reales.')
                value=complex(real.real,imag.real)
            else:
                source=row[start].replace('−','-').replace('π','pi')
                try:value=complex(source.replace('i','j').replace('I','j'))
                except ValueError:value=constant_value(source)
            if not np.isfinite(value):raise ValueError('La muestra debe ser finita.')
            values.append(value)
        except Exception as exc:raise ValueError('Fila '+str(i)+': '+str(exc)) from exc
    first=axis[0] if has_axis else integer_value(origin) if kind=='discrete' else real_value(origin)
    spacing=1 if kind=='discrete' else (axis[1]-axis[0] if has_axis and len(axis)>1 else real_value(step))
    if not math.isfinite(spacing) or spacing<=0:raise ValueError('El eje debe ser creciente y tener paso positivo.')
    if has_axis:
        for i,coordinate in enumerate(axis):
            expected=first+i*spacing
            if kind=='discrete':matches=coordinate==first+i
            else:
                tolerance=min(spacing/16,8*max(math.ulp(float(coordinate)),math.ulp(float(expected)),math.ulp(float(spacing))))
                matches=math.isfinite(expected) and abs(coordinate-expected)<=tolerance
            if not matches:raise ValueError('El eje no es uniforme en la fila '+str(i+1)+'. No se ordena ni remuestrea el pegado.')
    return Signal(values,first,spacing,units or ('n' if kind=='discrete' else 's' if kind=='continuous' else 'rad/muestra'),'Datos pegados',kind,'',dict(operation='pasted_samples',paste_layout=layout,decimal_comma=bool(decimal_comma),scope='Datos numéricos pegados y validados, sin ejecución de código.'))


def values_text(values):
    def cell(value):
        z=complex(value)
        if not z.imag:return format(z.real,'.17g')
        return '('+format(z.real,'.17g')+('+' if z.imag>=0 else '')+format(z.imag,'.17g')+'j)'
    return ', '.join(cell(value) for value in values)
