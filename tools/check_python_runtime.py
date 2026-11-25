"""Check that build and engineering tools are using the pinned CPython."""

from pathlib import Path
import platform


def require_pinned_python():
    pin = (Path(__file__).resolve().parents[1]/'.python-version').read_text(encoding='ascii').strip()
    actual = platform.python_version()
    if platform.python_implementation() != 'CPython' or actual != pin:
        raise SystemExit(f'Se requiere CPython {pin}. Se encontró {platform.python_implementation()} {actual}.')
    return pin


if __name__ == '__main__':
    print('CPython', require_pinned_python())
