"""Local custom palette configuration and readable accent selection."""
import json
from PySide6.QtGui import QColor

DEFAULT={'base':'navy','accent':'','photo':'','opacity':35,'fit':'cover','surface_opacity':100}


def validate(value):
    from .theme_presets import PRESETS
    value=value if isinstance(value,dict) else {};result=dict(DEFAULT)
    if value.get('base') in PRESETS and value['base']!='custom':result['base']=value['base']
    if isinstance(value.get('accent'),str) and QColor(value['accent']).isValid():result['accent']=QColor(value['accent']).name()
    if isinstance(value.get('photo'),str):result['photo']=value['photo']
    try:result['opacity']=min(100,max(0,int(value.get('opacity',35))))
    except (ValueError,TypeError):pass
    try:result['surface_opacity']=min(100,max(0,int(value.get('surface_opacity',100))))
    except (ValueError,TypeError):pass
    if value.get('fit') in ('cover','contain'):result['fit']=value['fit']
    return result


def load():
    from PySide6.QtCore import QSettings
    text=QSettings('SignalLab','Desktop071').value('appearance/custom','')
    try:return validate(json.loads(text)),bool(text)
    except (ValueError,TypeError):return dict(DEFAULT),False


def save(config):
    from PySide6.QtCore import QSettings
    QSettings('SignalLab','Desktop071').setValue('appearance/custom',json.dumps(validate(config),ensure_ascii=False))


def luminance(color):
    channels=QColor(color).getRgbF()[:3]
    linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in channels]
    return sum(a*b for a,b in zip(linear,(.2126,.7152,.0722)))


def contrast(a,b):
    one,two=sorted((luminance(a),luminance(b)))
    return (two+.05)/(one+.05)


def palette(config):
    from .theme_presets import PRESETS
    config=validate(config);colors=dict(PRESETS[config['base']][1]);accent=QColor(config['accent'] or colors['accent'])
    # Adjust brightness rather than allowing unreadable text on a chosen base.
    target=QColor('#111111' if luminance(colors['panel'])>.5 else '#f5f5f5')
    original=accent.getRgbF()[:3]
    for step in range(101):
        amount=step/100;candidate=QColor.fromRgbF(*[a*(1-amount)+b*amount for a,b in zip(original,target.getRgbF()[:3])])
        if min(contrast(candidate,colors[role]) for role in ('panel','report','chrome'))>=4.5:accent=candidate;break
    colors['accent']=accent.name();colors['primary']=accent.name()
    colors['primary_hover']=accent.lighter(110).name() if luminance(colors['panel'])<.5 else accent.darker(110).name()
    colors['on_primary']='#fffffd' if contrast(accent,'#fffffd')>contrast(accent,'#111215') else '#111215'
    return colors
