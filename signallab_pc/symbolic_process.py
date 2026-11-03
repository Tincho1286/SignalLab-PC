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
            notes=result.pop('_calculation_notes',[])
            if "error" in result: raise ValueError(result["error"])
            if notes:
                from .calculation_notes import merge,plain_text
                merge(notes)
                if request.get('operation') in ('cas_worksheet','cas_import'):
                    result.setdefault('notices',[]).append(plain_text(notes));result['calculation_notes']=notes
            return result
        finally:
            if process.poll() is None:
                process.terminate()
                try: process.wait(timeout=2)
                except subprocess.TimeoutExpired: process.kill(); process.wait()


def worker(source, destination):
    try:
        from .symbolic import execute
        from .calculation_notes import capture
        request=json.loads(Path(source).read_text(encoding='utf-8'))
        with capture() as records:result=execute(request)
        if isinstance(result,dict) and 'error' not in result and request.get('operation') in ('z_expression','z_finite','z_inverse_expression','laplace','inverse_laplace'):
            from .transform_steps import build
            result['derivation']=build(request,result)
        if isinstance(result,dict) and 'error' not in result:
            op=request.get('operation')
            if op in ('dtft_expression','inverse_dtft_expression','fourier_angular','inverse_fourier_angular'):
                from .quality_steps import fourier
                result['derivation']=fourier(request,result)
            elif op=='difference_equation':
                from .quality_steps import difference
                result['derivation']=difference(request,result)
            elif op=='ode':
                from .equation_checks import ode
                from .quality_steps import ode as ode_steps
                try:result['residual_check']=ode(request,result)
                except (ValueError,TypeError,NotImplementedError) as exc:result['residual_check']={'status':'Comprobación simbólica no disponible: '+str(exc)}
                result['derivation']=ode_steps(request,result)
        if records and isinstance(result,dict) and 'error' not in result:result['_calculation_notes']=list(records.values())
    except Exception as exc:
        result={"error":str(exc)}
    Path(destination).write_text(json.dumps(result,ensure_ascii=False),encoding="utf-8")
    return 1 if "error" in result else 0
