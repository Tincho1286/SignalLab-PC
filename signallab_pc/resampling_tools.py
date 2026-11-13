"""Plan rational rates from exact scalar input and describe the intermediate-rate FIR."""
import math,re
from .scalar_expression import exact_constant


def rate_ratio(input_rate,target):
    def clean(value):
        text=str(value).strip().replace('π','pi').replace('−','-')
        return text.replace(',','.') if re.fullmatch(r'[+-]?\d+,\d+',text) else text
    source=exact_constant(clean(input_rate));destination=exact_constant(clean(target))
    if source.is_real is not True or destination.is_real is not True or source.is_positive is not True or destination.is_positive is not True:
        raise ValueError('Las frecuencias de entrada y salida deben ser reales positivas.')
    ratio=(destination/source).cancel()
    if ratio.is_Rational is not True:
        raise ValueError('La tasa solicitada no define una relación racional exacta con la entrada. Elegí L/M para establecer una aproximación explícita.')
    return int(ratio.p),int(ratio.q)


def convert(source,up,down,*,target=None,**arguments):
    from .sampling import resample_rational
    if target is not None:
        rate=arguments.get('rate')
        if not arguments.get('override_clock') and source.metadata.get('sample_rate_hz') is not None:rate=source.metadata['sample_rate_hz']
        if rate is None:raise ValueError('Indicá la frecuencia de muestreo de entrada antes de elegir la de salida.')
        up,down=rate_ratio(rate,target)
    result,system,note=resample_rational(source,up,down,return_filter=True,**arguments)
    if target is not None:result.metadata['requested_rate_expression']=str(target)
    return dict(signal=result,filter=system,filter_note=note)


def summary(result,system,note=None):
    from .result_summary import signal_summary,Section,number
    summary=signal_summary(result);m=result.metadata;up=m['up'];down=m['down'];rate=m['input_rate_hz']
    rows=[('Relación irreducible L/M',str(up)+'/'+str(down)),('Fs de entrada (muestras/s)',number(rate)),('Fs de salida (muestras/s)',number(m['sample_rate_hz'])),('Longitud del FIR',str(m['filter_taps']))]
    if m.get('requested_rate_expression') is not None:rows.append(('Frecuencia de salida solicitada',m['requested_rate_expression']))
    if system is not None:
        rows.extend([('T de la rejilla intermedia (s)',number(system.sample_period_s)),('Ganancia DC del FIR',number(sum(system.b))),('Corte del ideal del diseño (rad/muestra intermedia)',number(math.pi/max(up,down)) if up!=down else 'Sin filtro · conversión identidad')])
    paragraphs=['El procesamiento combina expansión ↑L, FIR y reducción ↓M. El FIR se analiza sobre la rejilla intermedia, cuya tasa es Fs de entrada × L. Su ganancia incluye L para compensar la inserción de ceros.',
                'El cambio de tasa compensa el retardo del FIR para análisis fuera de tiempo real. Analizar o reutilizar el FIR conserva su retardo y su período intermedio; las muestras convertidas conservan su propio reloj de salida.']
    if up==down:paragraphs=['L/M=1: se conservan las muestras y se registra el reloj indicado. El sistema auxiliar es la identidad.']
    if note:paragraphs.append('La señal convertida se conserva. El sistema auxiliar no pudo representarse: '+note)
    summary.sections.append(Section('Conversión y filtro antialias',rows=rows,paragraphs=paragraphs));return summary
