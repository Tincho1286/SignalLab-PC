"""Build a Linux x86_64 portable from the same application sources as Windows."""
from pathlib import Path
from importlib import metadata
import ast,hashlib,json,os,platform,re,shutil,subprocess,sys,tarfile

ROOT=Path(__file__).resolve().parents[1]

def contained(path,parent):
    resolved=path.resolve();parent=parent.resolve()
    if resolved==parent or not resolved.is_relative_to(parent):raise ValueError('Generated path is outside its build directory.')
    if path.is_symlink():raise ValueError('Generated target must not be a symbolic link.')
    return resolved

def collect_notices(destination):
    shutil.copytree(ROOT/'LICENSES',destination,dirs_exist_ok=True)
    records=[]
    names=[]
    for line in (ROOT/'requirements-lock.txt').read_text(encoding='utf-8').splitlines():
        if '==' not in line:continue
        name=line.split('==',1)[0]
        try:dist=metadata.distribution(name)
        except metadata.PackageNotFoundError:continue  # Windows-only markers.
        if dist.metadata['Name'] in names:continue
        names.append(dist.metadata['Name']);copied=[]
        for entry in dist.files or []:
            relative=Path(str(entry));parts=[part.lower() for part in relative.parts]
            if relative.is_absolute() or '..' in relative.parts:continue
            if not ('licenses' in parts or relative.name.lower().startswith(('license','copying','notice','copyright','authors'))):continue
            source=Path(dist.locate_file(entry))
            if not source.is_file() or source.suffix.lower() in ('.py','.pyc','.so','.dll','.pyd'):continue
            target=destination/'linux-runtime'/name/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
            copied.append(target.relative_to(destination).as_posix())
        records.append({'name':dist.metadata['Name'],'version':dist.version,'license_expression':dist.metadata.get('License-Expression'),'notices':copied})
    (destination/'linux-runtime-manifest.json').write_text(json.dumps({'platform':platform.platform(),'python':platform.python_version(),'components':records},indent=2)+'\n',encoding='utf-8')

def sha256(path):
    result=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024**2),b''):result.update(block)
    return result.hexdigest()

def main():
    if sys.platform!='linux' or platform.machine().lower() not in ('x86_64','amd64'):raise SystemExit('Build this portable on Linux x86_64.')
    tree=ast.parse((ROOT/'signallab_pc/__init__.py').read_text(encoding='utf-8'))
    version=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='__version__' for t in n.targets))
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:[.+-][A-Za-z0-9.-]+)?',version):raise ValueError('Invalid source version.')
    build_root=ROOT/'work/linux-portable';build_root.mkdir(parents=True,exist_ok=True)
    intermediate=contained(build_root/'pyinstaller',build_root);staging=contained(build_root/'staging',build_root)
    package=contained(build_root/('SignalLab-PC-'+version+'-linux-x86_64'),build_root)
    if package.exists():shutil.rmtree(package)
    package.mkdir();legal=contained(build_root/'notices',build_root);legal.mkdir(exist_ok=True)
    collect_notices(legal)
    command=[sys.executable,'-B','-m','PyInstaller','--noconfirm','--clean','--onefile','--noupx','--name','SignalLab-PC','--distpath',str(staging),'--workpath',str(intermediate),'--specpath',str(build_root),
        '--add-data',str(ROOT/'signallab_pc/assets')+':signallab_pc/assets','--add-data',str(ROOT/'LICENSE')+':legal','--add-data',str(ROOT/'NOTICE.md')+':legal','--add-data',str(ROOT/'THIRD_PARTY_NOTICES.md')+':legal','--add-data',str(legal)+':legal/LICENSES',str(ROOT/'main.py')]
    subprocess.run(command,cwd=ROOT,check=True)
    binary=staging/'SignalLab-PC'
    with binary.open('rb') as stream:header=stream.read(64)
    if header[:4]!=b'\x7fELF' or header[4:6]!=b'\x02\x01' or int.from_bytes(header[18:20],'little')!=62:raise RuntimeError('The result is not a Linux x86_64 ELF executable.')
    binary.chmod(0o755);shutil.move(str(binary),str(package/'SignalLab-PC'))
    for name in ('LICENSE','NOTICE.md','THIRD_PARTY_NOTICES.md'):shutil.copy2(ROOT/name,package/name)
    shutil.copytree(legal,package/'LICENSES')
    readme=(ROOT/'docs/linux.md').read_text(encoding='utf-8')
    readme=re.sub(r'SignalLab-PC-\d+\.\d+\.\d+', 'SignalLab-PC-'+version, readme)
    readme=re.sub(r'SignalLab PC \d+\.\d+\.\d+', 'SignalLab PC '+version, readme)
    readme=re.sub(r'/releases/tag/v\d+\.\d+\.\d+(?:-preview)?', '/releases', readme)
    (package/'README.md').write_text(readme,encoding='utf-8',newline='\n')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    provenance={'application':'SignalLab PC','version':version,'platform':'linux','architecture':'x86_64','build_platform':platform.platform(),'glibc':platform.libc_ver(),'python':platform.python_version(),'source_commit':commit,'repository':'https://github.com/Tincho1286/SignalLab-PC','build_url':os.environ.get('BUILD_URL'),'binary_sha256':sha256(package/'SignalLab-PC'),'application_tests_run':False}
    (package/'build-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    outputs=ROOT/'outputs';outputs.mkdir(exist_ok=True)
    name=package.name+'.tar.gz';temporary=build_root/(name+'.partial');archive=outputs/name
    with tarfile.open(temporary,'w:gz',compresslevel=6) as tar:tar.add(package,arcname=package.name)
    os.replace(temporary,archive)
    provenance['archive_sha256']=sha256(archive);provenance['archive_name']=name
    (outputs/'build-provenance-linux.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    (outputs/('SHA256SUMS-linux-'+version+'.txt')).write_text(provenance['archive_sha256']+'  '+name+'\n',encoding='ascii')
    source=outputs/('SignalLab-PC-'+version+'-linux-source-GPL.zip')
    subprocess.run(['git','archive','--format=zip','--output',str(source),commit],cwd=ROOT,check=True)
    # Only remove generated paths whose final location was checked above.
    for generated in (intermediate,package,legal):
        contained(generated,build_root)
        if generated.exists():shutil.rmtree(generated)
    print('Generated:',archive,flush=True)

if __name__=='__main__':main()
