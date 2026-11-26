"""Install a build-only Pillow wheel without the unused JPEG 2000 decoder."""

from hashlib import file_digest
import os
from pathlib import Path
from shutil import copyfileobj
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory
from urllib.request import urlopen


PILLOW_VERSION = '13.0.0'
PILLOW_SOURCE = ('https://files.pythonhosted.org/packages/ce/a4/'
                 '9cc30690a394a8305e8be4c9036aa16d0dfddadd09079860b582f562496d/'
                 'pillow-13.0.0.tar.gz')
PILLOW_SHA256 = 'cdcd1ba258178f7356d74170c9a81ba4eab6a5d55748bc402a5a2a6fe6be3510'
WINDOWS_RECIPE = ('https://raw.githubusercontent.com/python-pillow/Pillow/'
                  '13.0.0/.github/dependencies.json')
WINDOWS_RECIPE_SHA256 = '63413d6dccf72367fc4c04c2560999e7a40ea14cf226dcc995d238cf3d25533b'
PILLOW_PROBE = (
    "from PIL import __version__, features; "
    f"assert __version__ == {PILLOW_VERSION!r}; "
    "assert all(features.check_codec(name) for name in ('jpg', 'zlib', 'libtiff')); "
    "assert features.check_module('webp'); "
    "assert not features.check_codec('jpg_2000')"
)
WHEEL_OPTIONS = (
    '--no-deps --no-build-isolation '
    '-C jpeg2000=disable -C avif=disable '
    '-C jpeg=enable -C zlib=enable -C tiff=enable -C webp=enable'
)


def download(url, destination, checksum):
    with urlopen(url, timeout=60) as response, destination.open('wb') as output:
        copyfileobj(response, output)
    with destination.open('rb') as stream:
        if file_digest(stream, 'sha256').hexdigest() != checksum:
            raise ValueError(f'El SHA-256 no coincide para {destination.name}.')


def windows_wheel(directory, source):
    # Use the pinned Pillow source's Windows recipes for the native dependencies.
    # Their generated paths stay in the fresh build directory.
    recipe_dir = source/'.github'
    recipe_dir.mkdir(exist_ok=True)
    download(WINDOWS_RECIPE, recipe_dir/'dependencies.json', WINDOWS_RECIPE_SHA256)
    launcher = directory/'build-pillow.cmd'
    launcher.write_text(
        '@echo off\n'
        'call "native\\build_dep_all.cmd" || exit /b 1\n'
        'call "native\\build_env.cmd" || exit /b 1\n'
        f'"%~1" -m pip wheel {WHEEL_OPTIONS} -C raqm=vendor -C fribidi=vendor '
        f'--wheel-dir wheels ".\\{source.name}"\n',
        encoding='ascii',
    )
    configure = (
        "import runpy; "
        "recipe = runpy.run_path('winbuild/build_prepare.py'); "
        "recipe['DEPS'].pop('openjpeg'); "
        "recipe['main']()"
    )
    subprocess.run(
        [sys.executable, '-B', '-c', configure, '--no-imagequant', '--no-avif',
         '--build-dir', str(directory/'native')],
        cwd=source, check=True,
    )
    subprocess.run(
        [os.environ['COMSPEC'], '/d', '/c', launcher.name, sys.executable],
        cwd=directory, check=True,
    )


def prepare_pillow():
    check = [sys.executable, '-B', '-c', PILLOW_PROBE]
    if subprocess.run(check, capture_output=True).returncode == 0:
        return
    subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '--no-deps',
         '--only-binary=:all:', 'pybind11==3.1.0'],
        check=True,
    )
    with TemporaryDirectory(prefix='sl-pillow-') as folder:
        directory = Path(folder)
        archive = directory/f'pillow-{PILLOW_VERSION}.tar.gz'
        download(PILLOW_SOURCE, archive, PILLOW_SHA256)
        wheels = directory/'wheels'
        if sys.platform == 'win32':
            with tarfile.open(archive) as source_archive:
                source_archive.extractall(directory, filter='data')
            windows_wheel(directory, directory/f'pillow-{PILLOW_VERSION}')
        else:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'wheel', *WHEEL_OPTIONS.split(),
                 '--wheel-dir', str(wheels), str(archive)],
                check=True,
            )
        (wheel,) = wheels.glob('pillow-*.whl')
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--no-deps', '--force-reinstall', str(wheel)],
            check=True,
        )
    subprocess.run(check, check=True)


if __name__ == '__main__':
    prepare_pillow()
