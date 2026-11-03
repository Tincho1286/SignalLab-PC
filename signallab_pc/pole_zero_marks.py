"""Consistent roots at their exact coordinates, above axes and polar grids."""
import numpy as np
from .theme_tokens import COLORS as C


def frame_root_plane(axis,zeros,poles,*,digital=False):
    """Keep a usable two-dimensional plane even for entirely real roots."""
    roots=np.r_[np.asarray(zeros,dtype=complex),np.asarray(poles,dtype=complex),0j]
    roots=roots[np.isfinite(roots)]
    if digital:roots=np.r_[roots,-1-1j,1+1j]
    xmin,xmax=float(np.min(roots.real)),float(np.max(roots.real));ymin,ymax=float(np.min(roots.imag)),float(np.max(roots.imag))
    cx=xmin/2+xmax/2;cy=ymin/2+ymax/2
    half=max(xmax/2-xmin/2,ymax/2-ymin/2)
    half=half*1.2 if half else 1.
    axis.set_xlim(cx-half,cx+half);axis.set_ylim(cy-half,cy+half)
    axis.set_aspect('equal',adjustable='box')


def origin_counts(zeros,poles):
    return int(np.count_nonzero(np.asarray(zeros)==0)),int(np.count_nonzero(np.asarray(poles)==0))


def origin_description(zeros,poles):
    nz,npoles=origin_counts(zeros,poles);parts=[]
    if nz:parts.append(str(nz)+(' cero' if nz==1 else ' ceros'))
    if npoles:parts.append(str(npoles)+(' polo' if npoles==1 else ' polos'))
    return 'Origen (0, 0): '+', '.join(parts) if parts else ''


def draw_root_markers(axis,zeros=(),poles=(),*,polar=False):
    axis._signallab_plane=True;axis._signallab_plane_label='Plano polar · θ (rad), r' if polar else 'Plano complejo · Re, Im'
    zeros=np.asarray(zeros,dtype=complex).reshape(-1);poles=np.asarray(poles,dtype=complex).reshape(-1)
    axis.set_axisbelow(True)
    if polar:axis.set_rorigin(0)
    def coordinates(values):
        if polar:
            # The angle of zero is undefined. Every angle at r=0 is the center;
            # use one consistent display coordinate without shifting the root.
            return np.where(values==0,0,np.mod(np.angle(values),2*np.pi)),np.abs(values)
        return values.real,values.imag
    artists=[]
    if zeros.size:
        artists.append(axis.scatter(*coordinates(zeros),marker='o',s=np.where(zeros==0,144,96),
            facecolors=C['panel'],edgecolors=C['blue'],linewidths=1.8,zorder=7,label='Ceros'))
    if poles.size:
        artists.append(axis.scatter(*coordinates(poles),marker='x',s=np.where(poles==0,100,76),
            color=C['amber'],linewidths=1.8,zorder=8,label='Polos'))
    description=origin_description(zeros,poles)
    if description:
        # The common figure layout places this information in the legend column,
        # so multiplicity remains readable without covering roots or moving them.
        axis.plot([],[],linestyle='none',color=C['muted'],label=description)
    return artists
