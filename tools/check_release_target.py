"""Validate the requested source and channel before native build jobs."""

import argparse
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from signallab_pc import __release_channel__, __version__
from signallab_pc.release_policy import publication_version


def validate(channel, reference, candidate, actual, version, source_channel):
    publication_version(version, channel)
    if not isinstance(candidate, str) or not re.fullmatch(r'[0-9a-f]{40}', candidate) or actual != candidate:
        raise ValueError('El SHA solicitado debe coincidir con el checkout.')
    if source_channel != channel:
        raise ValueError('El canal seleccionado debe coincidir con el código del candidato.')
    if channel == 'preview' and reference != 'refs/heads/develop':
        raise ValueError('La construcción Preview se ejecuta en develop.')
    if channel == 'stable' and reference not in ('refs/heads/main', f'refs/tags/v{version}'):
        raise ValueError('El paquete Stable/LTS necesita main con código LTS o su etiqueta exacta.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--channel', choices=('stable', 'preview'), required=True)
    parser.add_argument('--ref', required=True)
    parser.add_argument('--candidate', required=True)
    args = parser.parse_args()
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    validate(args.channel, args.ref, args.candidate, actual, __version__, __release_channel__)
    print('Verified', args.channel, __version__, actual)


if __name__ == '__main__':
    main()
