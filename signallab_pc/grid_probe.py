"""Read original scalar cells in images and rectilinear meshes, without interpolation."""
import numpy as np
from matplotlib.image import AxesImage
from matplotlib.collections import QuadMesh


def _cell(edges,value):
    if value is None or not np.isfinite(value):return None
    ordered=edges if edges[-1]>edges[0] else -edges
    value=value if edges[-1]>edges[0] else -value
    if value<ordered[0] or value>ordered[-1]:return None
    return min(int(np.searchsorted(ordered,value,side='right'))-1,len(edges)-2)


class GridTrace:
    spatial=True
    cell_values=True
    def __init__(self,axis,artist,xedges,yedges,values,revision):
        self.axis=axis;self.artist=artist;self.xedges=xedges;self.yedges=yedges;self.values=values;self.revision=revision
        colorbar=getattr(artist,'colorbar',None)
        self.label=colorbar.ax.get_ylabel() if colorbar is not None else ''
        if not self.label:
            label=artist.get_label();self.label=label if label and not label.startswith('_') else 'Valor de celda'

    @property
    def key(self):return id(self.artist)

    def point(self,x,y=None):
        column=_cell(self.xedges,x);row=_cell(self.yedges,y)
        if column is None or row is None:return None
        value=self.values[row,column]
        value=np.nan if np.ma.is_masked(value) else float(value)
        # Half each endpoint first, avoiding overflow in their sum.
        return (float(self.xedges[column]/2+self.xedges[column+1]/2),
                float(self.yedges[row]/2+self.yedges[row+1]/2),value)


def grid_trace(axis,artist):
    if not isinstance(artist,(AxesImage,QuadMesh)):return None
    values=artist.get_array()
    if values is None or np.asarray(values).dtype.kind not in 'biuf':return None
    if isinstance(artist,AxesImage):
        if values.ndim!=2 or artist.get_transform()!=axis.transData:return None
        rows,columns=values.shape
        if not rows or not columns:return None
        left,right,bottom,top=artist.get_extent()
        xedges=np.linspace(left,right,columns+1)
        yedges=np.linspace(top,bottom,rows+1) if artist.origin=='upper' else np.linspace(bottom,top,rows+1)
        revision=(id(values),tuple(artist.get_extent()),artist.origin)
    else:
        if artist.get_transform()!=axis.transData:return None
        coordinates=artist.get_coordinates()
        if coordinates.ndim!=3 or coordinates.shape[-1]!=2 or min(coordinates.shape[:2])<2:return None
        xedges=coordinates[0,:,0];yedges=coordinates[:,0,1]
        # A warped mesh has no unique rectangular-cell lookup. Do not guess.
        if not np.array_equal(coordinates[:,:,0],np.broadcast_to(xedges,coordinates.shape[:2])):return None
        if not np.array_equal(coordinates[:,:,1],np.broadcast_to(yedges[:,None],coordinates.shape[:2])):return None
        shape=(len(yedges)-1,len(xedges)-1)
        if values.size!=shape[0]*shape[1] or values.ndim>2:return None
        values=values.reshape(shape);revision=(id(artist.get_array()),id(coordinates))
    for edges in (xedges,yedges):
        if not np.isfinite(edges).all() or not (np.all(edges[1:]>edges[:-1]) or np.all(edges[1:]<edges[:-1])):return None
    return GridTrace(axis,artist,xedges,yedges,values,revision)
