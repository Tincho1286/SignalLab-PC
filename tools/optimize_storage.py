"""Remove verified build intermediates and share identical portable files.

Dry-run by default. Sources, environments, backups and executable paths survive.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,time,uuid


def checked(path,base):
    path=Path(path).absolute();base=Path(base).resolve(strict=True)
    if not path.is_relative_to(base) or path==base:
        raise ValueError('Target is outside its permitted parent: '+str(path))
    current=path
    while current!=base:
        if current.is_symlink() or (current.exists() and current.stat(follow_symlinks=False).st_file_attributes & 1024):
            raise ValueError('Reparse point is not a cleanup target: '+str(current))
        current=current.parent
    resolved=path.resolve(strict=True)
    if not resolved.is_relative_to(base) or resolved==base:
        raise ValueError('Resolved target is outside its permitted parent: '+str(path))
    return resolved


def files_no_links(folder):
    stack=[folder]
    while stack:
        current=stack.pop()
        for entry in os.scandir(current):
            stat=entry.stat(follow_symlinks=False)
            if entry.is_symlink() or stat.st_file_attributes & 1024:
                raise ValueError('Unexpected link in generated/portable folder: '+entry.path)
            path=Path(entry.path)
            if entry.is_dir(follow_symlinks=False):stack.append(path)
            elif entry.is_file(follow_symlinks=False):yield path,stat


def fingerprint(path):
    st=path.stat()
    return st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns


def digest(path):
    before=fingerprint(path);hasher=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024**2),b''):hasher.update(block)
    if fingerprint(path)!=before:raise ValueError('File changed during comparison: '+str(path))
    return hasher.hexdigest(),before


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--deliveries',type=Path)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args();root=args.root.resolve(strict=True)
    if not (root/'signallab_pc').is_dir() or not (root/'main.py').is_file():raise ValueError('Not a SignalLab PC project.')
    report={'timestamp':time.strftime('%Y-%m-%d %H:%M:%S'),'root':str(root),'apply':args.apply,'deleted_build_dirs':[],'shared_files':[],'unchanged_links':0,'errors':[]}
    before_free=shutil.disk_usage(root).free
    candidates=[]
    for base in (root/'work'/'pyinstaller',root/'build'):
        if not base.exists():continue
        checked(base,root)
        for path in base.iterdir():
            if not path.is_dir() or not path.name.startswith('SignalLab-PC'):continue
            path=checked(path,base)
            if not (path/'Analysis-00.toc').is_file():continue
            # Fully inspect before deletion; never follow junctions or symlinks.
            size=sum(st.st_size for _,st in files_no_links(path))
            candidates.append((base,path,size))
    print('Verified generated directories:',len(candidates),'; GiB:',round(sum(s for _,_,s in candidates)/2**30,3),flush=True)
    for base,path,size in candidates:
        checked(path,base)
        if args.apply:shutil.rmtree(path)
        report['deleted_build_dirs'].append({'path':str(path),'bytes':size})
    portable_roots=[root/'outputs',root/'releases',root/'dist',root/'work'/'portable-check']
    if args.deliveries:portable_roots.append(args.deliveries.resolve(strict=True))
    sized={}
    for folder in portable_roots:
        if not folder.exists():continue
        if folder.is_relative_to(root):checked(folder,root)
        for path,st in files_no_links(folder):
            if path.suffix.lower()=='.exe' and path.name.startswith('SignalLab'):
                checked(path,folder);sized.setdefault(st.st_size,[]).append((path,folder))
    groups={};total=sum(len(paths) for paths in sized.values());scanned=0
    for size,paths in sized.items():
        if len(paths)<2:continue
        for path,folder in paths:
            sha,stamp=digest(path);scanned+=1
            group=(size,sha)
            if group not in groups:groups[group]=(path,folder,stamp);continue
            source,source_folder,source_stamp=groups[group]
            if os.path.samefile(source,path):report['unchanged_links']+=1;continue
            if source.stat().st_dev!=path.stat().st_dev:continue
            shared={'source':str(source),'path':str(path),'bytes':size,'sha256':sha}
            if args.apply:
                temporary=path.with_name('.'+path.name+'.dedupe-'+uuid.uuid4().hex)
                try:
                    checked(path,folder);checked(source,source_folder)
                    if fingerprint(path)!=stamp or fingerprint(source)!=source_stamp:raise ValueError('A portable changed during cleanup.')
                    os.link(source,temporary)
                    if fingerprint(path)!=stamp:raise ValueError('Destination changed during cleanup.')
                    os.replace(temporary,path)
                    if not os.path.samefile(source,path):raise ValueError('Hard-link verification failed.')
                except OSError as exc:
                    report['errors'].append({'path':str(path),'error':str(exc)})
                    continue
                finally:
                    if temporary.exists():temporary.unlink()
            report['shared_files'].append(shared)
            if len(report['shared_files'])%20==0:print('Identical copies shared:',len(report['shared_files']),flush=True)
    report['before_free_bytes']=before_free;report['after_free_bytes']=shutil.disk_usage(root).free
    report['reclaimed_bytes']=report['after_free_bytes']-before_free
    target=root/'work'/'storage-maintenance.json'
    if args.apply:
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Identical copies:',len(report['shared_files']),'; already linked:',report['unchanged_links'],'; errors:',len(report['errors']),flush=True)
    print('Actual reclaimed GiB:',round(report['reclaimed_bytes']/2**30,3),'; free GiB:',round(report['after_free_bytes']/2**30,3),flush=True)
    if args.apply:print('Manifest:',target,flush=True)


if __name__=='__main__':main()
