"""Aislamiento del CAS para permitir cancelación sin terminar la interfaz."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from .jobs import checkpoint


def run_request(request):
    with tempfile.TemporaryDirectory(prefix="signallab-cas-") as directory:
        source=Path(directory)/"request.json"; destination=Path(directory)/"result.json"
        source.write_text(json.dumps(request),encoding="utf-8")
        entry=[sys.executable] if getattr(sys,"frozen",False) else [sys.executable,str(Path(__file__).resolve().parent.parent/"main.py")]
        command=entry+["--symbolic-job",str(source),str(destination)]
        process=subprocess.Popen(command, cwd=directory, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        try:
            while process.poll() is None:
                checkpoint()
                try: process.wait(timeout=.1)
                except subprocess.TimeoutExpired: pass
            checkpoint()
            if not destination.exists(): raise RuntimeError("El proceso simbólico terminó sin un resultado; revisá la expresión y los recursos disponibles.")
            result=json.loads(destination.read_text(encoding="utf-8"))
            if "error" in result: raise ValueError(result["error"])
            return result
        finally:
            if process.poll() is None:
                process.terminate()
                try: process.wait(timeout=2)
                except subprocess.TimeoutExpired: process.kill(); process.wait()


def worker(source, destination):
    try:
        from .symbolic import execute
        result=execute(json.loads(Path(source).read_text(encoding="utf-8")))
    except Exception as exc:
        result={"error":str(exc)}
    Path(destination).write_text(json.dumps(result,ensure_ascii=False),encoding="utf-8")
    return 1 if "error" in result else 0
