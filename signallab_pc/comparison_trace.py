"""Captured common coordinates for differences, plots and CSV export."""
import csv
import numpy as np
from .atomic_file import atomic_text_file


def capture(coordinates,a,b,*,units,label,discrete=False,index=False):
    coordinates=np.array(coordinates,copy=True);a=np.array(a,dtype=complex,copy=True);b=np.array(b,dtype=complex,copy=True)
    if coordinates.ndim!=1 or a.shape!=coordinates.shape or b.shape!=coordinates.shape:raise ValueError('Las coordenadas comunes y sus valores deben coincidir.')
    finite=np.isfinite(a)&np.isfinite(b)
    with np.errstate(over='ignore',invalid='ignore',under='ignore'):error=b-a
    overflow=finite&~np.isfinite(error);error[~finite|overflow]=complex(np.nan,np.nan)
    for values in (coordinates,a,b,error):values.flags.writeable=False
    return dict(coordinates=coordinates,a=a,b=b,error=error,units=units,label=label,discrete=bool(discrete),index=bool(index),
                undefined_count=int((~finite).sum()),overflow_count=int(overflow.sum()))


def export_csv(path,trace,impulses=None):
    parts=[('parte ordinaria',trace)]+([('peso de Dirac',impulses)] if impulses is not None else [])
    if not any(len(data['coordinates']) for _,data in parts):raise ValueError('No hay coordenadas almacenadas comunes para exportar una diferencia.')
    with atomic_text_file(path,encoding='utf-8-sig',newline='') as stream:
        writer=csv.writer(stream,delimiter=';')
        writer.writerow(['coordenada ('+trace['units']+')','A real','A imaginaria','B real','B imaginaria','B-A real','B-A imaginaria','parte','estado'])
        for part,data in parts:
            for x,a,b,e in zip(data['coordinates'],data['a'],data['b'],data['error']):
                state='finito' if np.isfinite(e) else 'fuera de rango float64' if np.isfinite([a,b]).all() else 'entrada no definida'
                def components(z):return [format(z.real,'.17g'),format(z.imag,'.17g')] if np.isfinite(z) else ['','']
                coordinate=str(int(x)) if data['index'] else format(float(x),'.17g')
                writer.writerow([coordinate,*components(a),*components(b),*components(e),part,state])
