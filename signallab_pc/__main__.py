"""Entry points for the desktop and the headless DFT."""

import sys


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == ['dft']:
        from .dft_cli import main as dft
        return dft(args[1:])
    if args[:1] == ['dsp-pipeline']:
        from .dsp_pipeline_cli import main as pipeline
        return pipeline(args[1:])
    if args[:1] == ['dsp']:
        from .dsp_cli import main as dsp
        return dsp(args[1:])
    if len(args) == 3 and args[0] == '--symbolic-job':
        from .symbolic_process import worker
        return worker(args[1], args[2])
    if len(args) == 2 and args[0] == '--matlab-job':
        from .matlab_process import worker
        return worker(args[1])
    if len(args) == 2 and args[0] == '--self-check':
        from .self_check import run
        return run(args[1])
    if args[:1] == ['--install-linux']:
        from .linux_installer_ui import main as install
        return install(args[1:])
    from .ui import main as desktop
    return desktop()


if __name__ == '__main__':
    raise SystemExit(main())
