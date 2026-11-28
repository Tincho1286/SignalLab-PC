"""Shared colors for the scientific desktop, reports, figures and help."""
COLORS = {
    'window':'#0e1320', 'chrome':'#131a2a', 'panel':'#192238',
    'input':'#101827', 'report':'#121b2d', 'hover':'#26334b',
    'border':'#354661', 'rule':'#273650', 'grid':'#2d4160',
    'text':'#edf3fc', 'muted':'#b2c1d8', 'disabled':'#8194b0',
    'accent':'#a6b9ff', 'selected':'#273a5e', 'primary':'#b0c2ff',
    'primary_hover':'#c6d4ff', 'on_primary':'#102145',
    'green':'#74dfc0', 'amber':'#ffc289', 'blue':'#8cc1ff',
    'purple':'#c9abfb', 'red':'#f3aeb7', 'cyan':'#83d8ed',
}

AREA_COLORS = {
    'signals':COLORS['green'], 'systems':COLORS['blue'],
    'filters':COLORS['purple'], 'spectra':COLORS['amber'],
    'sampling':COLORS['cyan'], 'transforms':COLORS['accent'],
    'random':COLORS['red'], 'communications':COLORS['amber'], 'rf':COLORS['cyan'],
}


def colorize(template):
    for key,value in COLORS.items():template=template.replace('@'+key+'@',value)
    return template
