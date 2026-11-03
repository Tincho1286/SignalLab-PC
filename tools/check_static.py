"""Block undefined names and local-variable failures before packaging."""
from pathlib import Path
import ast,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
FATAL={'UndefinedName','UndefinedLocal','DuplicateArgument','ForwardAnnotationSyntaxError'}

def import_bindings(node):
    return {a.asname or (a.name.split('.')[0] if isinstance(node,ast.Import) else a.name) for a in node.names}

def local_nodes(node):
    yield node
    for child in ast.iter_child_nodes(node):
        if not isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef,ast.Lambda)):yield from local_nodes(child)

def conditional_imports(tree,filename):
    module_names=set().union(*(import_bindings(n) for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))))
    issues=[]
    for function in ast.walk(tree):
        if not isinstance(function,(ast.FunctionDef,ast.AsyncFunctionDef)):continue
        excluded={n for b in function.body for k in local_nodes(b) if isinstance(k,(ast.Global,ast.Nonlocal)) for n in k.names}
        excluded.update(a.arg for a in [*function.args.posonlyargs,*function.args.args,*function.args.kwonlyargs])
        for block in function.body:
            if isinstance(block,(ast.Import,ast.ImportFrom)):continue
            for node in local_nodes(block):
                if not isinstance(node,(ast.Import,ast.ImportFrom)):continue
                for name in import_bindings(node)&module_names-excluded:
                    outside=any(isinstance(k,ast.Name) and isinstance(k.ctx,ast.Load) and k.id==name for b in function.body if b is not block for k in local_nodes(b))
                    if outside:issues.append(filename+':'+str(node.lineno)+': conditional local import shadows module name '+repr(name)+' used outside its block; use the module import or a distinct alias')
    return issues

def inspect(source,filename):
    from pyflakes.checker import Checker
    try:
        tree=ast.parse(source,filename=filename)
        return [str(m) for m in Checker(tree,filename=filename).messages if type(m).__name__ in FATAL]+conditional_imports(tree,filename)
    except (SyntaxError,ValueError) as exc:return [filename+': '+str(exc)]

def paths(root=ROOT):return [root/'main.py',*sorted((root/'signallab_pc').rglob('*.py'))]

def fingerprint(root=ROOT):
    digest=hashlib.sha256()
    for p in [*paths(root),root/'tools/check_static.py',root/'requirements-quality.txt']:
        digest.update(p.relative_to(root).as_posix().encode());digest.update(b'\0');digest.update(p.read_bytes().replace(b'\r\n',b'\n'));digest.update(b'\0')
    return digest.hexdigest()

def main():
    import pyflakes
    files=paths();issues=[]
    for p in files:issues.extend(inspect(p.read_text(encoding='utf-8-sig'),str(p.relative_to(ROOT))))
    # A broken checker must never count a zero-length report as a clean scan.
    probes=["def f():\n return absent_name", "from math import floor\ndef f(inverse):\n if inverse:\n  from math import floor\n  return floor(1)\n return floor(2)"]
    checker_verified=all(inspect(source,'probe') for source in probes)
    passed=not issues and len(files)>=200 and checker_verified
    report=dict(contract='static-action-names-v1',passed=passed,files=len(files),issues=issues,checker_verified=checker_verified,pyflakes=pyflakes.__version__,source_fingerprint=fingerprint())
    folder=ROOT/'work';folder.mkdir(exist_ok=True);(folder/'static-checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    for issue in issues:print(issue)
    print('Static action guard: '+('PASS' if passed else 'FAIL')+' · '+str(len(files))+' Python files')
    return 0 if passed else 1

if __name__=='__main__':raise SystemExit(main())
