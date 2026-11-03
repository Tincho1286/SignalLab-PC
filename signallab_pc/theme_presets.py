"""Dark appearance presets; tokens stay shared by reference throughout the app."""
import re
from .theme_tokens import COLORS,AREA_COLORS

DEFAULT=dict(COLORS)
PRESETS={
    'navy':('Azul marino',dict(DEFAULT)),
    'graphite':('Grafito',{**DEFAULT,'window':'#17191d','chrome':'#1c1f24','panel':'#252a31','input':'#191d22','report':'#20242b','hover':'#343c46','border':'#495461','rule':'#343b45','grid':'#414b57','text':'#edf0f4','muted':'#b9c1cc','disabled':'#8995a4','accent':'#97c8ee','selected':'#354859','primary':'#9cccef','primary_hover':'#badff7','on_primary':'#142430','green':'#93d5bc','amber':'#e5c291','blue':'#9cbef1','purple':'#c9b6e7','red':'#e5a6af','cyan':'#9bd7de'}),
    'forest':('Bosque',{**DEFAULT,'window':'#101d1a','chrome':'#142721','panel':'#1c352d','input':'#11231d','report':'#172b25','hover':'#2a4b3e','border':'#3f6655','rule':'#29483c','grid':'#365947','text':'#e4f2e9','muted':'#acc8b8','disabled':'#789d8a','accent':'#b0d99b','selected':'#31513c','primary':'#a5d99c','primary_hover':'#c0ebae','on_primary':'#152516','green':'#83d5b2','amber':'#e8ca8c','blue':'#9fc4e2','purple':'#c4b3df','red':'#e3aba1','cyan':'#8ed4ce'}),
    'aubergine':('Berenjena',{**DEFAULT,'window':'#1b1423','chrome':'#241c30','panel':'#30263f','input':'#20192b','report':'#282033','hover':'#443653','border':'#645076','rule':'#43354f','grid':'#51415e','text':'#f0e9f7','muted':'#c5b5d4','disabled':'#9987ab','accent':'#d4b2f2','selected':'#503b62','primary':'#c9a8ef','primary_hover':'#e0c6fa','on_primary':'#25152f','green':'#96d6bc','amber':'#ebc294','blue':'#a9bff0','purple':'#c3a2e2','red':'#e9a8c2','cyan':'#a2d5e5'}),
}
CURRENT='navy'


def select(key):
    global CURRENT
    if key not in PRESETS:key='navy'
    COLORS.clear();COLORS.update(PRESETS[key][1]);CURRENT=key
    for area,role in [('signals','green'),('systems','blue'),('filters','purple'),('spectra','amber'),('sampling','cyan'),('transforms','accent'),('random','red')]:AREA_COLORS[area]=COLORS[role]
    return key


def color(value,previous=None):
    mapping={}
    palettes=[previous] if previous is not None else [DEFAULT,*[entry[1] for entry in PRESETS.values()]]
    for palette in palettes:
        mapping.update({old.lower():COLORS[role] for role,old in palette.items()})
    mapping.setdefault('#e1e7ee',COLORS['text'])
    return mapping.get(str(value).lower(),value)


def recolor(text,previous=None):
    return re.sub(r'#[0-9a-fA-F]{6}(?![0-9a-fA-F])',lambda m:color(m.group(),previous),str(text))


def restore():
    from PySide6.QtCore import QSettings
    return select(QSettings('SignalLab','Desktop071').value('appearance/theme','navy'))
