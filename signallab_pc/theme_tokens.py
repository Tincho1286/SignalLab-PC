"""Shared colors for the scientific desktop, reports, figures and help."""
COLORS = {
    'window':'#0e1417', 'chrome':'#131c20', 'panel':'#182429',
    'input':'#101a1e', 'report':'#141f23', 'hover':'#223438',
    'border':'#3c555a', 'rule':'#2a3d42', 'grid':'#30464b',
    'text':'#eaf3f2', 'muted':'#aabfc0', 'disabled':'#7d9295',
    'accent':'#79e5c7', 'selected':'#1d3b36', 'primary':'#8defd4',
    'primary_hover':'#b3f6e5', 'on_primary':'#102b27',
    'green':'#84dec2', 'amber':'#ffbd82', 'blue':'#97c3f6',
    'purple':'#c6b5ef', 'red':'#f3a7ac', 'cyan':'#92d8ed',
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
