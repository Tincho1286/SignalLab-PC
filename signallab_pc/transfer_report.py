"""Readable transfer equations which fit the result pane at its current width."""
import re
from PySide6.QtCore import QTimer
from .vector_math import render_latex
from .math_display import latex
from .report_view import ReportView
from .theme_tokens import COLORS


def equation_formula(left,right,size=15):return render_latex(latex(left)+' = '+latex(right),size=size,color=COLORS['text'])



class TransferResultReport(ReportView):
    def __init__(self,parent=None):
        super().__init__(parent);self.summary=None;self._last_width=None;self._resize_pending=False;self._reflowing=False;self._render_width=None;self._resize_anchor=None
        self._resize_timer=QTimer(self);self._resize_timer.setSingleShot(True);self._resize_timer.setInterval(35);self._resize_timer.timeout.connect(self._fit_equations)
    def set_readable(self,summary):
        self._resize_timer.stop();self._resize_pending=False;self._resize_anchor=None;self.summary=summary;self._render_width=self._last_width=self.viewport().width();self._reflowing=True
        try:super().set_readable(summary)
        finally:self._reflowing=False
        self._queue_fit()
    def setPlainText(self,text):
        self.summary=None;self._resize_timer.stop();self._resize_pending=False;self._resize_anchor=None;self._render_width=self._last_width=self.viewport().width();super().setPlainText(text)
    def _render_formula(self,source,numeric=False,leading_dot=False,math_size=15):
        equation=re.fullmatch(r'([A-Za-z]+\([sz]\))\s*=\s*(.+)',source.strip())
        if equation and len(source)<=2000 and not numeric and not leading_dot:
            try:
                formula=equation_formula(*equation.groups(),size=math_size)
                width=max(1,min(formula.width,max(100,(self._render_width or self.viewport().width())-45)))
                return self.vector_math_html(formula,source,width)
            except (ValueError,RuntimeError,RecursionError,SyntaxError):pass
        return super()._render_formula(source,numeric=numeric,leading_dot=leading_dot,math_size=math_size)
    def resizeEvent(self,event):
        # Qt rewraps the document in its resize handler. Capture the old reading
        # position before that handler, not after the debounce timer expires.
        if self.summary is not None and not self._reflowing and self._resize_anchor is None:self._resize_anchor=self.reading_anchor()
        super().resizeEvent(event)
        self._queue_fit()
        if not self._resize_pending:self._resize_anchor=None
    def _queue_fit(self):
        if self.summary is not None and not self._reflowing and self.viewport().width()!=self._last_width:
            self._resize_pending=True;self._resize_timer.start()
    def _fit_equations(self):
        self._resize_pending=False
        if self.summary is None or self.viewport().width()==self._last_width:
            self._resize_anchor=None;return
        anchor=self._resize_anchor or self.reading_anchor();self._resize_anchor=None;self._render_width=self._last_width=self.viewport().width();self._reflowing=True
        try:
            super().set_readable(self.summary);self.restore_reading_anchor(anchor)
        finally:self._reflowing=False
        self._queue_fit()

