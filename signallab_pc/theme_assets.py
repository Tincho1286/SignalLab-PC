"""Small local SVG controls, tinted for both light and dark backgrounds."""
from pathlib import Path
import re
from PySide6.QtCore import QStandardPaths
from .theme_tokens import COLORS


def paths():
    folder=Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.GenericCacheLocation))/'SignalLab'/'theme-icons';folder.mkdir(parents=True,exist_ok=True)
    result=[]
    for name in ('chevron_technical','close_document'):
        target=folder/(name+'-'+COLORS['muted'].lstrip('#')+'.svg')
        if not target.exists():
            text=(Path(__file__).parent/'assets'/(name+'.svg')).read_text(encoding='utf-8')
            target.write_text(re.sub(r'#[0-9a-fA-F]{6}',COLORS['muted'],text),encoding='utf-8')
        result.append(target.as_posix())
    return result
