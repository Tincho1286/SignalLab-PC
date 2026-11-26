"""Validate the requested source and channel before native build jobs."""

import argparse
import ast
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from signallab_pc.release_policy import publication_version


def validate(channel, reference, candidate, actual, version, source_channel):
    publication_version(version, channel)
    if not isinstance(candidate, str) or not re.fullmatch(r'[0-9a-f]{40}', candidate) or actual != candidate:
        raise ValueError('El SHA solicitado debe identificar un commit exacto.')
    if source_channel != channel:
        raise ValueError('El canal seleccionado debe coincidir con el código del candidato.')
    if channel == 'preview' and reference != 'refs/heads/develop':
        raise ValueError('La construcción Preview se ejecuta en develop.')
    if channel == 'stable' and reference not in ('refs/heads/main', f'refs/tags/v{version}'):
        raise ValueError('El paquete Stable/LTS necesita main con código LTS o su etiqueta exacta.')


def validate_history(channel, candidate, tip):
    if not all(isinstance(sha, str) and re.fullmatch(r'[0-9a-f]{40}', sha) for sha in (candidate, tip)):
        raise ValueError('La ejecución debe identificar los SHA completos del candidato y de la referencia.')
    if channel == 'stable':
        if candidate != tip:
            raise ValueError('Stable/LTS se construye desde el SHA exacto de la referencia seleccionada.')
    elif subprocess.run(['git', 'merge-base', '--is-ancestor', candidate, tip], cwd=ROOT).returncode:
        raise ValueError('El candidato Preview debe pertenecer al historial de develop.')


def revision_metadata(source):
    keys = {'__version__', '__release_channel__'}
    metadata = {}
    for statement in ast.parse(source).body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name) and target.id in keys:
                    metadata[target.id] = ast.literal_eval(statement.value)
    if set(metadata) != keys:
        raise ValueError('El candidato debe declarar versión y canal en el código.')
    return metadata['__version__'], metadata['__release_channel__']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--channel', choices=('stable', 'preview'), required=True)
    parser.add_argument('--ref', required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--ref-tip', required=True)
    args = parser.parse_args()
    tip = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if tip != args.ref_tip:
        raise ValueError('La comprobación requiere el checkout de la referencia seleccionada.')
    validate_history(args.channel, args.candidate, args.ref_tip)
    actual = subprocess.check_output(['git', 'rev-parse', args.candidate+'^{commit}'], cwd=ROOT, text=True).strip()
    source = subprocess.check_output(['git', 'show', actual+':signallab_pc/__init__.py'], cwd=ROOT, encoding='utf-8')
    version, channel = revision_metadata(source)
    validate(args.channel, args.ref, args.candidate, actual, version, channel)
    print('Verified', args.channel, version, actual)


if __name__ == '__main__':
    main()
