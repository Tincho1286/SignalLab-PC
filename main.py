"""Entrada única de escritorio y diagnóstico del ejecutable portable."""
import sys

if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--symbolic-job":
        from signallab_pc.symbolic_process import worker
        raise SystemExit(worker(sys.argv[2], sys.argv[3]))
    if len(sys.argv) == 3 and sys.argv[1] == "--self-check":
        from signallab_pc.self_check import run
        raise SystemExit(run(sys.argv[2]))
    if len(sys.argv) >= 2 and sys.argv[1] == "--install-linux":
        from signallab_pc.linux_installer_ui import main
        raise SystemExit(main(sys.argv[2:]))
    from signallab_pc.ui import main
    main()
