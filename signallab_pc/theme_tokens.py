"""Shared colors for the scientific desktop, reports, figures and help."""
COLORS = {
    'window':'#0d1016', 'chrome':'#12161e', 'panel':'#1c222d',
    'input':'#121821', 'report':'#171d27', 'hover':'#2a3241',
    'border':'#374052', 'rule':'#29313f', 'grid':'#333d4e',
    'text':'#f1f3f9', 'muted':'#aeb7c8', 'disabled':'#758094',
    'accent':'#c2b2ff', 'selected':'#36304f', 'primary':'#bca6ff',
    'primary_hover':'#d2c3ff', 'on_primary':'#1c1530',
    'green':'#8bdec7', 'amber':'#f0c78d', 'blue':'#a1c1ff',
    'purple':'#c7b3ff', 'red':'#efadbf', 'cyan':'#96dce7',
}

AREA_COLORS = {
    'signals':COLORS['green'], 'systems':COLORS['blue'],
    'filters':COLORS['purple'], 'spectra':COLORS['amber'],
    'sampling':COLORS['cyan'], 'transforms':COLORS['accent'],
    'random':COLORS['red'],
}


def colorize(template):
    for key,value in COLORS.items():template=template.replace('@'+key+'@',value)
    return template
