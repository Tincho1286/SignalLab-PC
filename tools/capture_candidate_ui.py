"""Prepare audit views at explicit logical sizes and Qt scale factors."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PROFILES = ((640,480,1), (800,600,1.25), (960,640,1.5), (1280,800,1))


def capture(output, width, height, hold):
    from PySide6.QtCore import QSettings, QStandardPaths
    from PySide6.QtWidgets import QApplication
    from signallab_pc.cas_reference import CAS_ROUTE
    from signallab_pc.sampling import sample_expression
    from signallab_pc.workbench import WorkbenchWindow
    from signallab_pc.workspaces import ROUTES

    app = QApplication([])
    app.setStyle('Fusion')
    output.mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory(prefix='signallab-ui-review-') as folder:
        profile = Path(folder)
        QSettings.setDefaultFormat(QSettings.Format.IniFormat)
        QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, folder)
        with patch.object(QStandardPaths,'writableLocation', side_effect=lambda loc: str(profile/loc.name)):
            window = WorkbenchWindow(recovery_directory=profile)
            window.resize(width,height)
            window.show()
            app.processEvents()
            if hold:
                return app.exec()
            sampling = ROUTES['sampling',0]
            for name, route in (('inicio',None), ('muestreo',sampling), ('cas',CAS_ROUTE)):
                if route is not None:
                    window.open_tool(route)
                if route==sampling:
                    panel = window.pages[tuple(route)].panel
                    panel._accept_signal(sample_expression('cos(2*pi*t)',0,32,65))
                app.processEvents()
                if not window.grab().save(str(output/f'{name}.png')):
                    raise RuntimeError('No se pudo guardar la vista de auditoría.')
            screen = window.screen()
            (output/'profile.json').write_text(json.dumps(dict(
                qt_platform=app.platformName(), window=[window.width(),window.height()],
                screen=[screen.size().width(),screen.size().height()], scale=screen.devicePixelRatio(),
                dpi=screen.logicalDotsPerInch(), views=['inicio','muestreo','cas']),indent=2)+'\n')
            window.project.dirty = False
            window.close()
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--size', type=int, nargs=2)
    parser.add_argument('--hold', action='store_true')
    args = parser.parse_args()
    if args.size:
        return capture(args.output, *args.size, args.hold)
    for width, height, scale in PROFILES:
        target = args.output / f'{width}x{height}-{scale}'
        env = os.environ | {'QT_SCALE_FACTOR':str(scale)}
        if sys.platform=='linux':
            env['QT_QPA_PLATFORM'] = 'xcb'
        subprocess.run([sys.executable,'-B',__file__,'--output',str(target),'--size',
                        str(width),str(height)],env=env,check=True,timeout=75)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
