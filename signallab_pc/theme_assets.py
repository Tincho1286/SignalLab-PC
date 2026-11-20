"""Small local SVG controls, tinted for both light and dark backgrounds."""
from pathlib import Path
import re
from PySide6.QtCore import QStandardPaths
from .theme_tokens import COLORS


def paths():
    folder=Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.GenericCacheLocation))/'SignalLab'/'theme-icons';folder.mkdir(parents=True,exist_ok=True)
    result=[]
    for name,role in (('chevron_technical','muted'),('close_document','muted'),
                      ('check_indicator','on_primary'),('mixed_indicator','on_primary')):
        color=COLORS[role]
        target=folder/(name+'-'+color.lstrip('#')+'.svg')
        if not target.exists():
            text=(Path(__file__).parent/'assets'/(name+'.svg')).read_text(encoding='utf-8')
            target.write_text(re.sub(r'#[0-9a-fA-F]{6}',color,text),encoding='utf-8')
        result.append(target.as_posix())
    return result
