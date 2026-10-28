"""Compare one fitted cascade against its target, on common frequency axes."""
import numpy as np
from .theme_tokens import COLORS as C
from .signal_plot import configure_axis,plot_samples


def draw_comparison(panel,data):
    mode=panel.system_view.currentIndex();figure=panel.view.figure;figure.clear()
    axes=np.atleast_1d(figure.subplots(3 if mode==0 else 1,1,sharex=True));w=data['omega']
    inside=(w>=data['low'])&(w<=data['high']);desired=data['gain']*np.exp(-1j*w*data['delay'])
    source=data['input'];compensator=data['compensator']
    source_delay=source.group_delay(w) if mode in (0,2) else np.zeros(len(w))
    delays=(source_delay,source_delay+compensator.group_delay(w) if mode in (0,2) else source_delay,np.full(len(w),data['delay'],float))
    labels=('Módulo (dB)','Error de fase (rad)','Retardo de grupo (muestras)') if mode==0 else ('Módulo (dB)',) if mode==1 else ('|H| · amplitud',) if mode==3 else ('Retardo de grupo (muestras)',)
    for h,delay,label,color,is_target in zip((data['original'],data['joint'],desired),delays,('Original H','Compensado H·C','Objetivo en la banda'),(C['muted'],C['green'],C['amber']),(False,False,True)):
        amplitude=abs(h);valid=np.isfinite(h)&(amplitude>0)
        db=np.full(len(w),np.nan);db[valid]=20*np.log10(amplitude[valid])
        phase_error=np.full(len(w),np.nan);mask=valid&inside;phase_error[mask]=np.angle(h[mask]/desired[mask])
        delay=np.asarray(delay).copy();delay[~valid]=np.nan
        magnitude=amplitude.copy()
        if is_target:
            for vector in (db,magnitude,delay):vector[~inside]=np.nan
        values=(db,phase_error,delay) if mode==0 else (db,) if mode==1 else (magnitude,) if mode==3 else (delay,)
        for index,(axis,values_to_plot) in enumerate(zip(axes,values)):
            lines=plot_samples(axis,w,values_to_plot,label=label,color=color,phase=mode==0 and index==1)
            for line in lines:line.set_linestyle('--' if is_target else '-');line.set_linewidth(1.4 if is_target else 1.8)
    for axis,label in zip(axes,labels):
        axis.set_ylabel(label);axis.grid(alpha=.2);axis.axvspan(data['low'],data['high'],color=C['blue'],alpha=.07)
        axis.set_xlim(0,np.pi)
    if mode==0:
        axes[1].set_ylim(-np.pi,np.pi);axes[1].set_yticks([-np.pi,-np.pi/2,0,np.pi/2,np.pi],['−π','−π/2','0','π/2','π'])
    axes[0].legend(fontsize=8);configure_axis(axes[-1],units='rad/muestra',label='ω (rad/muestra)')
    figure.set_layout_engine('constrained');panel.view.canvas.draw_idle()
    panel.view.text.setPlainText('Comparación del último diseño\n\nLa banda sombreada es la región de ajuste. El objetivo sólo se dibuja allí. El error de fase se mide respecto de ganancia·exp(−iωD), como ángulo principal, y se omite en ceros. La respuesta y el retardo de la cascada se evalúan con H y C por separado. Los botones de sistemas actúan sobre el resultado elegido en el selector.')


def compensation_help_image():
    from PySide6.QtCore import Qt,QRectF,QLineF
    from PySide6.QtGui import QImage,QPainter,QColor,QFont,QPen
    image=QImage(960,300,QImage.Format.Format_ARGB32);image.fill(QColor(C['report']));p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x,y,w,h,value,color='text',size=14):
        p.setPen(QColor(C[color]));p.setFont(QFont('Segoe UI',size));p.drawText(QRectF(x,y,w,h),Qt.TextFlag.TextWordWrap,value)
    def arrow(x,y,end,color):
        p.setPen(QPen(QColor(C[color]),2));p.drawLine(QLineF(x,y,end,y));p.drawLine(QLineF(end-9,y-6,end,y));p.drawLine(QLineF(end-9,y+6,end,y))
    text(30,8,900,40,'Compensar la respuesta de la cascada en una banda',size=18)
    text(35,78,120,48,'Entrada',size=15);arrow(140,100,235,'muted')
    for x,label,color in [(240,'H(z)\nSistema original','blue'),(570,'C(z)\nCompensador FIR','green')]:
        p.setPen(QPen(QColor(C[color]),2));p.drawRect(QRectF(x,60,220,85));text(x+12,69,196,70,label,color,15)
    arrow(465,100,565,'green');arrow(795,100,885,'green');text(880,75,75,60,'Salida',size=13)
    text(35,165,890,44,'Objetivo: H·C ≈ ganancia · exp(−iωD) en la banda elegida','amber',17)
    text(35,216,425,76,'D permite un retardo causal. El diseño busca aproximar módulo y fase juntos.','muted',13)
    text(505,216,425,76,'λ penaliza coeficientes grandes. El error medido indica cuánto se logró aproximar.','muted',13)
    p.end();return image


