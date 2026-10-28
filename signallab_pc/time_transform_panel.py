"""Continuous routes of the common signal transformation panel."""
from .signal_transform_panel import SignalTransformPanel
class TimeTransformPanel(SignalTransformPanel):
    def __init__(self,window,index=0):
        super().__init__(window,'continuous',{0:'affine',1:'shift',2:'reverse',3:'scale',4:'parity'}[index])
