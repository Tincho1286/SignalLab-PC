"""Readable transfer equations which fit the result pane at its current width."""
import re
from PySide6.QtCore import QTimer
from .vector_math import render_latex
from .math_display import latex
from .report_view import ReportView
from .theme_tokens import COLORS


def equation_formula(left,right):return render_latex(latex(left)+' = '+latex(right),color=COLORS['text'])



class TransferResultReport(ReportView):
    def __init__(self,parent=None):
        super().__init__(parent);self.summary=None;self._last_width=None;self._resize_pending=False
    def set_readable(self,summary):
        self.summary=summary;self._last_width=self.viewport().width();super().set_readable(summary)
    def _render_formula(self,source,numeric=False,leading_dot=False):
        equation=re.fullmatch(r'([A-Za-z]+\([sz]\))\s*=\s*(.+)',source.strip())
        if equation and len(source)<=2000 and not numeric and not leading_dot:
            try:
                formula=equation_formula(*equation.groups())
                width=max(1,min(formula.width,max(100,self.viewport().width()-45)))
                return self.vector_math_html(formula,source,width)
            except (ValueError,RuntimeError,RecursionError,SyntaxError):pass
        return super()._render_formula(source,numeric=numeric,leading_dot=leading_dot)
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if self.summary is not None and self.viewport().width()!=self._last_width and not self._resize_pending:
            self._resize_pending=True;QTimer.singleShot(0,self,self._fit_equations)
    def _fit_equations(self):
        self._resize_pending=False
        if self.summary is None:return
        bar=self.verticalScrollBar();position=bar.value()/max(1,bar.maximum());self.set_readable(self.summary)
        QTimer.singleShot(0,self,lambda:self.verticalScrollBar().setValue(round(position*self.verticalScrollBar().maximum())))

