"""Persistencia de intercambio: JSON preserva complejos, eje y metadatos."""

import math
import csv
import json
from pathlib import Path

from .model import Signal
from .atomic_file import atomic_text_file,write_json


def save_json(signal: Signal, path: str | Path) -> None:
    document = {
        "format": "signallab-signal", "schema_version": 1,
        "name": signal.name, "domain": signal.domain, "origin": signal.origin,
        "step": signal.step, "units": signal.units, "expression": signal.expression,
        "metadata": signal.metadata,
        "samples": [[float(v.real), float(v.imag)] for v in signal.values],
    }
    write_json(path,document)


def load_json(path: str | Path) -> Signal:
    from .resources import ensure_working_set
    ensure_working_set(Path(path).stat().st_size,bytes_per_sample=1,live_arrays=8)
    doc = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(doc,dict) or doc.get("format") != "signallab-signal" or doc.get("schema_version") != 1:
        raise ValueError("El JSON no tiene un formato SignalLab compatible.")
    missing=[key for key in ('samples','origin','step','units','name','domain') if key not in doc]
    if missing:raise ValueError('La señal está incompleta. Faltan: '+', '.join(missing)+'.')
    if not isinstance(doc['samples'],list) or any(not isinstance(pair,list) or len(pair)!=2 for pair in doc['samples']):raise ValueError('Cada muestra debe contener un par [real, imaginaria].')
    import numpy as np
    try:
        samples = np.asarray([complex(re, im) for re, im in doc["samples"]], dtype=complex)
        return Signal(samples, doc["origin"], float(doc["step"]), doc["units"],
                      doc["name"], doc["domain"], doc.get("expression", ""), doc.get("metadata", {}))
    except (TypeError,ValueError,OverflowError) as exc:raise ValueError('Definición de señal inválida: '+str(exc)) from exc


def save_csv(signal: Signal, path: str | Path) -> None:
    with atomic_text_file(path,newline="",encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["# SignalLab CSV v1", f"name={signal.name}", f"domain={signal.domain}",
                        "origin=" + (str(signal.origin) if signal.domain == "discrete" else format(signal.origin, ".17g")), f"step={signal.step:.17g}", f"units={signal.units}", "metadata="+json.dumps(signal.metadata,ensure_ascii=False,allow_nan=False)])
        writer.writerow(["axis", "real", "imag"])
        for index,value in enumerate(signal.values):
            axis=signal.origin+index if signal.domain=="discrete" else signal.origin+index*signal.step
            if not math.isfinite(axis):raise ValueError("El eje excede el rango numérico; no se modificó el archivo de destino.")
            writer.writerow([str(int(axis)) if signal.domain == "discrete" else f"{axis:.17g}", f"{value.real:.17g}", f"{value.imag:.17g}"])


def load_csv(path,*,domain='discrete',delimiter=',',skip_rows=1,axis_column=0,real_column=1,imag_column=None,decimal_comma=False,origin=0,step=1,axis_units=None):
    """Importa CSV propio o columnas explícitas; no remuestrea ejes irregulares."""
    import math
    from decimal import Decimal,InvalidOperation
    from .resources import ensure_working_set
    if delimiter not in (',',';','\t'):raise ValueError('Separador no admitido.')
    if decimal_comma and delimiter==',':raise ValueError('Para coma decimal elegí punto y coma o tabulación como separador.')
    path=Path(path);metadata={};name=path.stem;units={'discrete':'n','continuous':'s','frequency':'rad/s'}.get(domain,'n')
    values=[];first=None;spacing=None;previous=None;axis_scale=1
    source_units=axis_units or units
    with path.open('r',newline='',encoding='utf-8-sig') as stream:
        first_line=stream.readline();stream.seek(0)
        own=first_line.startswith('# SignalLab CSV v1')
        reader=csv.reader(stream,delimiter=',' if own else delimiter)
        if own:
            header=next(reader);fields=dict(cell.split('=',1) for cell in header[1:] if '=' in cell)
            domain=fields['domain'];name=fields.get('name',name);units=fields.get('units',units);metadata=json.loads(fields.get('metadata','{}'))
            origin=fields.get('origin','0');step=float(fields.get('step','1'));axis_column=0;real_column=1;imag_column=2;decimal_comma=False
            if next(reader,None)!=['axis','real','imag']:raise ValueError('Encabezado de columnas SignalLab inválido.')
        else:
            for _ in range(skip_rows):next(reader,None)
        if domain not in ('discrete','continuous','frequency'):raise ValueError('Dominio CSV no admitido.')
        if not own:
            choices={'discrete':{'n':('n',1)},'continuous':{'s':('s',1),'ms':('s',1e-3),'us':('s',1e-6)},'frequency':{'rad/s':('rad/s',1),'rad/sample':('rad/muestra',1),'rad/muestra':('rad/muestra',1)}}
            if source_units not in choices[domain]:raise ValueError('Las unidades no corresponden al dominio elegido.')
            units,axis_scale=choices[domain][source_units]
        def number(value):
            value=value.strip().replace(',','.') if decimal_comma else value.strip()
            result=float(value)
            if not math.isfinite(result):raise ValueError('Los datos deben ser finitos.')
            return result
        def coordinate(value):
            if domain!='discrete':return number(str(value))
            parsed=Decimal(str(value).strip().replace(',','.') if decimal_comma else str(value).strip())
            if not parsed.is_finite() or parsed!=parsed.to_integral_value():raise ValueError('Una secuencia requiere índices enteros. Para tiempos medidos usá una entrada continua.')
            return int(parsed)
        generated_origin=coordinate(origin)
        descending=own and domain!='discrete' and float(step)<0
        if not math.isfinite(float(step)) or float(step)==0 or not descending and float(step)<0 or domain=='discrete' and float(step)!=1:raise ValueError('El paso debe ser positivo; en secuencias discretas debe ser 1. Un CSV propio conserva también su eje descendente.')
        for row in reader:
            if not row or all(not cell.strip() for cell in row):continue
            try:
                if len(values)%4096==0:ensure_working_set(len(values)+4096,bytes_per_sample=128,live_arrays=4)
                value=complex(number(row[real_column]),number(row[imag_column]) if imag_column is not None else 0)
                axis=coordinate(row[axis_column]) if axis_column is not None else generated_origin+len(values)*(1 if domain=='discrete' else step)
                if domain!='discrete' and not math.isfinite(axis):raise ValueError('El eje excede el rango numérico finito.')
                if first is None:first=axis
                else:
                    delta=axis-previous
                    if delta==0 or (delta>0 if descending else delta<0):raise ValueError('El eje no conserva la dirección indicada; no se reordenan las muestras.')
                    if spacing is None:spacing=step if own else delta
                    expected=first+len(values)*spacing
                    tolerance=0 if domain=='discrete' else max(abs(spacing)*1e-7,8*math.ulp(float(expected)))
                    if abs(axis-expected)>tolerance or (domain=='discrete' and delta!=1):raise ValueError('El eje no tiene paso uniforme. No se interpolan ni descartan datos automáticamente.')
                previous=axis;values.append(value)
            except (ValueError,IndexError,InvalidOperation) as exc:raise ValueError(f'Fila CSV {reader.line_num}: {exc}') from exc
    if not values:raise ValueError('No hay muestras para importar. Revisá encabezados y columnas.')
    actual_step=1 if domain=='discrete' else spacing if spacing is not None else float(step)
    if own and (first!=generated_origin or not math.isclose(actual_step,float(step),rel_tol=1e-7,abs_tol=0)):
        raise ValueError('El eje del CSV no coincide con su encabezado SignalLab.')
    if not own and domain!='discrete':
        first*=axis_scale;actual_step*=axis_scale
        if not math.isfinite(first) or not math.isfinite(actual_step) or actual_step<=0:raise ValueError('El eje convertido excede la precisión numérica disponible.')
    return Signal(values,first,actual_step,units,name,domain,'',metadata if own else {'operation':'import_csv','source_file':path.name,'uniform_axis':True,'source_axis_units':source_units})
