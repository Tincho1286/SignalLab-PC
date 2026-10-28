"""Shared colors for the scientific desktop, reports, figures and help."""
COLORS = {
    'window':'#101725', 'chrome':'#141e2e', 'panel':'#1b293d',
    'input':'#111c2b', 'report':'#152132', 'hover':'#263950',
    'border':'#354962', 'rule':'#28394e', 'grid':'#354862',
    'text':'#e8eef8', 'muted':'#adbbd0', 'disabled':'#788ba5',
    'accent':'#a5baff', 'selected':'#2a4163', 'primary':'#8faaff',
    'primary_hover':'#b0c2ff', 'on_primary':'#101a2d',
    'green':'#83dbc5', 'amber':'#efc38d', 'blue':'#95b9ff',
    'purple':'#c2adf5', 'red':'#e7a6b9', 'cyan':'#8bd4e8',
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
