"""Appearance presets; tokens stay shared by reference throughout the app."""
import re
from .theme_tokens import COLORS,AREA_COLORS

DEFAULT=dict(COLORS)
PRESETS={
    'navy':('Azul marino',dict(DEFAULT)),
    'graphite':('Grafito',{**DEFAULT,'window':'#17191d','chrome':'#1c1f24','panel':'#252a31','input':'#191d22','report':'#20242b','hover':'#343c46','border':'#495461','rule':'#343b45','grid':'#414b57','text':'#edf0f4','muted':'#b9c1cc','disabled':'#8995a4','accent':'#97c8ee','selected':'#354859','primary':'#9cccef','primary_hover':'#badff7','on_primary':'#142430','green':'#93d5bc','amber':'#e5c291','blue':'#9cbef1','purple':'#c9b6e7','red':'#e5a6af','cyan':'#9bd7de'}),
    'forest':('Bosque',{**DEFAULT,'window':'#101d1a','chrome':'#142721','panel':'#1c352d','input':'#11231d','report':'#172b25','hover':'#2a4b3e','border':'#3f6655','rule':'#29483c','grid':'#365947','text':'#e4f2e9','muted':'#acc8b8','disabled':'#789d8a','accent':'#b0d99b','selected':'#31513c','primary':'#a5d99c','primary_hover':'#c0ebae','on_primary':'#152516','green':'#83d5b2','amber':'#e8ca8c','blue':'#9fc4e2','purple':'#c4b3df','red':'#e3aba1','cyan':'#8ed4ce'}),
    'aubergine':('Berenjena',{**DEFAULT,'window':'#1b1423','chrome':'#241c30','panel':'#30263f','input':'#20192b','report':'#282033','hover':'#443653','border':'#645076','rule':'#43354f','grid':'#51415e','text':'#f0e9f7','muted':'#c5b5d4','disabled':'#9987ab','accent':'#d4b2f2','selected':'#503b62','primary':'#c9a8ef','primary_hover':'#e0c6fa','on_primary':'#25152f','green':'#96d6bc','amber':'#ebc294','blue':'#a9bff0','purple':'#c3a2e2','red':'#e9a8c2','cyan':'#a2d5e5'}),
}
PRESETS.update({'vanta': ('Vanta Black', {'window': '#000000', 'chrome': '#030303', 'panel': '#070707', 'input': '#010101', 'report': '#050505', 'hover': '#171718', 'border': '#343438', 'rule': '#202024', 'grid': '#242428', 'text': '#f2f2f4', 'muted': '#bfc0c5', 'disabled': '#85858d', 'accent': '#adbaf2', 'selected': '#23232a', 'primary': '#aebbf4', 'primary_hover': '#c4cef9', 'on_primary': '#111217', 'green': '#8ed9bb', 'amber': '#eac58e', 'blue': '#a5bdf2', 'purple': '#cbb5ef', 'red': '#e8a9bf', 'cyan': '#9bd6df'}), 'pink': ('Rosa', {'window': '#25151f', 'chrome': '#301c29', 'panel': '#3b2634', 'input': '#2a1a24', 'report': '#321f2c', 'hover': '#503346', 'border': '#78576b', 'rule': '#503748', 'grid': '#594050', 'text': '#f9eaf2', 'muted': '#d8b7ca', 'disabled': '#aa8499', 'accent': '#f2acd1', 'selected': '#613b52', 'primary': '#ec9ac5', 'primary_hover': '#f6bfdf', 'on_primary': '#301321', 'green': '#a4ddc4', 'amber': '#ebc7a3', 'blue': '#b4c8f0', 'purple': '#d9b7ec', 'red': '#f1a5ba', 'cyan': '#a3dbe1'}), 'light': ('Claro', {'window': '#edf1f6', 'chrome': '#e5eaf1', 'panel': '#f8fafc', 'input': '#ffffff', 'report': '#fdfefe', 'hover': '#e1e8f2', 'border': '#b2c0d0', 'rule': '#d4dce6', 'grid': '#d8e0ea', 'text': '#172435', 'muted': '#475970', 'disabled': '#718096', 'accent': '#2b52a3', 'selected': '#d9e5f8', 'primary': '#315fb3', 'primary_hover': '#284e94', 'on_primary': '#fffffd', 'green': '#176855', 'amber': '#81571b', 'blue': '#2f5daa', 'purple': '#6e489b', 'red': '#a13b59', 'cyan': '#176c7d'}), 'white': ('Blanco', {'window': '#ffffff', 'chrome': '#fafafa', 'panel': '#fefefe', 'input': '#fcfcfc', 'report': '#fdfefe', 'hover': '#f2f4f7', 'border': '#bec7d4', 'rule': '#dde2e9', 'grid': '#e1e6ee', 'text': '#171d26', 'muted': '#4d5766', 'disabled': '#778292', 'accent': '#214d91', 'selected': '#e6edf8', 'primary': '#2255aa', 'primary_hover': '#174689', 'on_primary': '#fffffd', 'green': '#16644b', 'amber': '#835717', 'blue': '#285ca8', 'purple': '#73489d', 'red': '#a23c50', 'cyan': '#1f6c7e'})})
PRESETS['custom']=('Personalizado',dict(DEFAULT))
CUSTOM={'base':'navy','accent':'','photo':'','opacity':35,'fit':'cover'}
HAS_CUSTOM=False

CURRENT='navy'


def select(key):
    global CURRENT
    if key not in PRESETS:key='navy'
    COLORS.update(PRESETS[key][1]);CURRENT=key
    for area,role in [('signals','green'),('systems','blue'),('filters','purple'),('spectra','amber'),('sampling','cyan'),('transforms','accent'),('random','red')]:AREA_COLORS[area]=COLORS[role]
    return key


def color(value,previous=None,kind=None):
    value=str(value).lower()
    if kind:
        roles=('text','muted','accent','green','amber','blue','purple','red','cyan','disabled','on_primary') if kind=='foreground' else ('border','rule','grid') if kind=='border' else ('report','panel','window','input','chrome','selected','hover')
        if value in (COLORS[r].lower() for r in roles):return value
        for palette in [DEFAULT,*[entry[1] for entry in PRESETS.values()]]:
            for role in roles:
                if palette[role].lower()==value:return COLORS[role]
        return value
    mapping={}
    palettes=[previous] if previous is not None else [DEFAULT,*[entry[1] for entry in PRESETS.values()]]
    for palette in palettes:mapping.update({old.lower():COLORS[role] for role,old in palette.items()})
    mapping['#e1e7ee']=COLORS['text']
    return mapping.get(value,value)


def recolor(text,previous=None):
    return re.sub(r'#[0-9a-fA-F]{6}(?![0-9a-fA-F])',lambda m:color(m.group(),previous),str(text))


def restore():
    from PySide6.QtCore import QSettings
    global HAS_CUSTOM
    from .custom_appearance import load
    config,HAS_CUSTOM=load();set_custom(config)
    return select(QSettings('SignalLab','Desktop071').value('appearance/theme','navy'))


def set_custom(config):
    global CUSTOM
    from .custom_appearance import validate,palette
    CUSTOM=validate(config);PRESETS['custom']=('Personalizado',palette(CUSTOM))
