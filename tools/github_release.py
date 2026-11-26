"""Publish SignalLab releases with an explicit public-repository opt-in using Git's existing GitHub session."""
from pathlib import Path
import argparse,hashlib,http.client,json,os,re,subprocess,sys,urllib.request,urllib.error,urllib.parse

REPOSITORY='Tincho1286/SignalLab-PC'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def sha256(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024**2),b''):digest.update(block)
    return digest.hexdigest()


def validate_publication_files(tag, target, channel, paths, gate):
    """Bind the approved commit, checksums and candidate receipts before mutation."""
    from signallab_pc.release_policy import publication_version
    from signallab_pc.update_manifest import FILENAMES

    if not isinstance(tag, str) or not tag.startswith('v'):
        raise ValueError('La etiqueta debe comenzar con v y contener la versión numérica.')
    version = tag[1:]
    publication_version(version, channel)
    if not re.fullmatch(r'[0-9a-f]{40}', target):
        raise ValueError('Indicá el SHA completo validado.')
    if not isinstance(gate, dict) or gate.get('commit') != target or gate.get('automated_passed') is not True:
        raise ValueError('La evidencia del Quality Gate debe aprobar el SHA de la publicación.')
    platforms = gate.get('platforms', {})
    if not isinstance(platforms, dict) or not {'windows-2022', 'ubuntu-22.04'} <= platforms.keys():
        raise ValueError('El Quality Gate requiere evidencia de Windows y Linux.')
    files = {path.name: path for path in paths}
    if len(files) != len(paths):
        raise ValueError('Cada adjunto debe tener un nombre distinto.')
    checksums = f'SHA256SUMS-{version}.txt'
    source = f'SignalLab-PC-{version}-source.zip'
    expected = {'SignalLab-updates.json', checksums, source, 'candidate-windows.json', 'candidate-linux.json',
                f'SignalLab-PC-{version}.exe', f'SignalLab-PC-{version}-linux-x86_64.tar.gz',
                'installer-windows.json', 'installer-linux.json', *[item.format(version=version) for item in FILENAMES.values()]}
    if missing := expected - files.keys():
        raise ValueError('Faltan adjuntos verificados: ' + ', '.join(sorted(missing)))
    calculated = {name: sha256(path) for name, path in files.items() if name != checksums}
    declared = {}
    for line in files[checksums].read_text(encoding='utf-8-sig').splitlines():
        match = re.fullmatch(r'([0-9a-fA-F]{64}) [ *]([^/\\]+)', line)
        if match is None or match[2] in declared:
            raise ValueError('El archivo de checksums tiene una entrada inválida o repetida.')
        declared[match[2]] = match[1].lower()
    if declared != calculated:
        raise ValueError('Los checksums no coinciden con todos los adjuntos de la publicación.')
    fingerprints = set()
    for platform in ('windows', 'linux'):
        receipt = json.loads(files[f'candidate-{platform}.json'].read_text(encoding='utf-8-sig'))
        if (receipt.get('commit'), receipt.get('version'), receipt.get('channel'), receipt.get('platform')) != (
            target, version, channel, platform,
        ):
            raise ValueError('Los comprobantes de preparación deben corresponder al canal y al SHA aprobado.')
        fingerprint = receipt.get('source_fingerprint')
        if not isinstance(fingerprint, str) or not re.fullmatch(r'[0-9a-f]{64}', fingerprint):
            raise ValueError('Falta la huella de los archivos de origen.')
        fingerprints.add(fingerprint)
        portable = f'SignalLab-PC-{version}.exe' if platform == 'windows' else f'SignalLab-PC-{version}-linux-x86_64.tar.gz'
        installer = FILENAMES[f'{platform}-x86_64'].format(version=version)
        names = {portable, installer, f'installer-{platform}.json'}
        declarations = receipt.get('files', {})
        if not names <= declarations.keys() or any(
            name not in files or proof != {'sha256': calculated.get(name), 'size': files[name].stat().st_size}
            for name, proof in declarations.items()
        ):
            raise ValueError('Los adjuntos difieren de la construcción verificada.')
        if platform == 'windows' and source not in declarations:
            raise ValueError('El archivo de fuentes requiere un comprobante de construcción.')
    if len(fingerprints) != 1:
        raise ValueError('Los dos empaquetados deben corresponder a las mismas fuentes.')


def require_publication_checkout(root, target, channel, lts_base):
    def git(*arguments):
        return subprocess.check_output(['git', *arguments], cwd=root, text=True).strip()

    if git('status', '--porcelain') or git('rev-parse', 'HEAD') != target:
        raise ValueError('La publicación requiere un checkout limpio en el SHA aprobado.')
    arguments = ['git', 'merge-base', '--is-ancestor']
    if channel == 'preview':
        remote = git('ls-remote', 'origin', 'refs/heads/develop').split()
        if not remote or subprocess.run([*arguments, target, remote[0]], cwd=root).returncode:
            raise ValueError('El SHA de la preliminar debe formar parte de develop en GitHub.')
    else:
        if git('rev-parse', '--abbrev-ref', 'HEAD') != 'HEAD' or not lts_base:
            raise ValueError('Prepará el mantenimiento desde la última etiqueta LTS en un checkout desacoplado.')
        if not re.fullmatch(r'v2\.0\.(0|[1-9][0-9]*)', lts_base):
            raise ValueError('La base de mantenimiento debe ser una etiqueta LTS v2.0.x.')
        upstream = git('ls-remote', '--tags', 'origin', f'refs/tags/{lts_base}', f'refs/tags/{lts_base}^{{}}').splitlines()
        if not upstream:
            raise ValueError('No se encontró en GitHub la etiqueta LTS de origen.')
        base_commit = next((row.split()[0] for row in upstream if row.endswith('^{}')), upstream[0].split()[0])
        if subprocess.run([*arguments, base_commit, target], cwd=root).returncode:
            raise ValueError('El candidato LTS debe descender de la etiqueta de mantenimiento indicada.')


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        redirected=super().redirect_request(req,fp,code,msg,headers,newurl)
        if redirected and urllib.parse.urlsplit(req.full_url).netloc!=urllib.parse.urlsplit(newurl).netloc:
            redirected.remove_header('Authorization')
        return redirected


class GitHub:
    def __init__(self,repository=REPOSITORY):
        self.repository=repository
        env=os.environ.copy();env['GIT_TERMINAL_PROMPT']='0';env['GCM_INTERACTIVE']='never'
        result=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,env=env,timeout=30)
        data=dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
        if result.returncode or not data.get('password'):raise RuntimeError('Git no tiene una sesión de GitHub disponible. Iniciá sesión y repetí la publicación.')
        self._token=data['password'];self.opener=urllib.request.build_opener(SafeRedirect())

    def headers(self):
        return {'Authorization':'Bearer '+self._token,'Accept':'application/vnd.github+json','User-Agent':'SignalLab-release-tool','X-GitHub-Api-Version':'2022-11-28'}

    def api(self,method,path,body=None):
        url='https://api.github.com'+path
        data=json.dumps(body).encode() if body is not None else None
        request=urllib.request.Request(url,data=data,headers=self.headers(),method=method)
        if data is not None:request.add_header('Content-Type','application/json')
        with self.opener.open(request,timeout=60) as response:
            raw=response.read();return json.loads(raw) if raw else None

    def require_repository(self,allow_public=False):
        repo=self.api('GET','/repos/'+self.repository)
        if repo.get('full_name','').casefold()!=self.repository.casefold():raise RuntimeError('GitHub devolvió otro repositorio; no se publica.')
        if repo.get('private') is not True and not (allow_public and repo.get('visibility')=='public'):
            raise RuntimeError('La publicación pública requiere autorización explícita mediante --allow-public.')
        return repo

    def require_private(self):
        return self.require_repository()

    def assets(self,release):
        result=[];page=1
        while True:
            batch=self.api('GET',f'/repos/{self.repository}/releases/{release["id"]}/assets?per_page=100&page={page}')
            result.extend(batch)
            if len(batch)<100:return result
            page+=1

    def verify(self,asset,path,expected=None):
        path=Path(path);expected=expected or sha256(path)
        remote=self.api('GET',f'/repos/{self.repository}/releases/assets/{asset["id"]}')
        if remote['state']!='uploaded' or remote['size']!=path.stat().st_size:raise RuntimeError('Tamaño remoto incompleto: '+path.name)
        digest=remote.get('digest')
        if digest:
            if digest!='sha256:'+expected:raise RuntimeError('SHA-256 remoto diferente: '+path.name)
        else:
            request=urllib.request.Request(remote['url'],headers=self.headers())
            request.add_header('Accept','application/octet-stream');hasher=hashlib.sha256();count=0
            with self.opener.open(request,timeout=60) as stream:
                for block in iter(lambda:stream.read(4*1024**2),b''):hasher.update(block);count+=len(block)
            if count!=path.stat().st_size or hasher.hexdigest()!=expected:raise RuntimeError('La descarga no coincide: '+path.name)
        return remote

    def upload(self,release,path):
        path=Path(path);expected=sha256(path)
        existing=next((a for a in self.assets(release) if a['name']==path.name),None)
        if existing:return self.verify(existing,path,expected)
        size=path.stat().st_size
        if size>=2*1024**3:raise ValueError('El archivo supera el límite de 2 GiB por adjunto: '+path.name)
        url=urllib.parse.urlsplit(release['upload_url'].split('{',1)[0]+'?'+urllib.parse.urlencode({'name':path.name}))
        if url.scheme!='https' or url.netloc!='uploads.github.com':raise RuntimeError('Destino de subida inesperado.')
        connection=http.client.HTTPSConnection(url.netloc,timeout=60)
        try:
            connection.putrequest('POST',url.path+'?'+url.query)
            for key,value in self.headers().items():connection.putheader(key,value)
            connection.putheader('Content-Type','application/octet-stream');connection.putheader('Content-Length',str(size));connection.endheaders()
            print('Uploading:',path.name,'MiB:',round(size/2**20,2),flush=True)
            with path.open('rb') as stream:
                for block in iter(lambda:stream.read(1024**2),b''):connection.send(block)
            response=connection.getresponse();raw=response.read()
            if response.status!=201:raise RuntimeError('GitHub rechazó la subida (HTTP '+str(response.status)+').')
            asset=json.loads(raw)
        finally:connection.close()
        result=self.verify(asset,path,expected)
        print('Verified:',path.name,expected,flush=True);return result

    def ensure_release_tag(self,tag,target,title,*,detached_lts=False):
        """Date new annotated tags with GitHub's clock, preserving existing refs."""
        base='/repos/'+self.repository;reference=base+'/git/ref/tags/'+urllib.parse.quote(tag,safe='')
        try:
            existing=self.api('GET',reference)['object']
        except urllib.error.HTTPError as exc:
            if exc.code!=404:raise
        else:
            while existing['type']=='tag':existing=self.api('GET',base+'/git/tags/'+existing['sha'])['object']
            if existing['type']!='commit' or existing['sha']!=target:raise RuntimeError('La etiqueta existente apunta a otro commit; no se modifica.')
            return
        from datetime import timezone
        from email.utils import parsedate_to_datetime
        request=urllib.request.Request('https://api.github.com'+base,headers=self.headers())
        with self.opener.open(request,timeout=60) as response:server_date=response.headers.get('Date')
        if not server_date:raise RuntimeError('GitHub no informó su fecha; no se usa el reloj local para fechar la etiqueta.')
        date=parsedate_to_datetime(server_date).astimezone(timezone.utc)
        maintainer=self.api('GET','/user')
        login=maintainer['login']
        address=str(maintainer['id'])+'+'+login+'@users.noreply.github.com'
        message=title+'\n\nBuild source commit: '+target+'.'
        if detached_lts:
            # Transmit the detached commit and its tag together. The commit need not be on a remote branch.
            obj = f'object {target}\ntype commit\ntag {tag}\ntagger {login} <{address}> {int(date.timestamp())} +0000\n\n{message}\n'
            identity = subprocess.check_output(['git', 'mktag'], cwd=ROOT, input=obj, encoding='utf-8').strip()
            subprocess.run(['git', 'push', '--no-follow-tags', f'https://github.com/{self.repository}.git',
                            f'{identity}:refs/tags/{tag}'], cwd=ROOT, check=True)
            return
        annotated=self.api('POST',base+'/git/tags',{'tag':tag,'message':message,'object':target,'type':'commit','tagger':{'name':login,'email':address,'date':date.strftime('%Y-%m-%dT%H:%M:%SZ')}})
        self.api('POST',base+'/git/refs',{'ref':'refs/tags/'+tag,'sha':annotated['sha']})

    def publish(self,tag,title,notes,paths,target,prerelease=True,allow_public=False,*,gate=None,lts_base=None):
        paths=[Path(path) for path in paths]
        channel = 'preview' if prerelease else 'stable'
        if any(path.name.endswith(('-setup.exe','-linux-x86_64.run')) for path in paths):
            from signallab_pc.update_manifest import verify_manifest
            manifests=[path for path in paths if path.name=='SignalLab-updates.json']
            if len(manifests)!=1:raise ValueError('La entrega instalable necesita su manifiesto firmado de actualización.')
            manifest=verify_manifest(manifests[0].read_bytes(),expected_channel=channel)
            if tag!='v'+manifest.version:raise ValueError('La etiqueta debe coincidir con la versión numérica firmada.')
            from signallab_pc.update_manifest import FILENAMES
            if set(manifest.assets) != set(FILENAMES):
                raise ValueError('El manifiesto firmado debe contener los instaladores de ambos sistemas.')
            for asset in manifest.assets.values():
                matches=[path for path in paths if path.name==asset.name]
                if len(matches)!=1 or matches[0].stat().st_size!=asset.size or sha256(matches[0])!=asset.sha256:
                    raise ValueError('Falta un instalador o no coincide con el manifiesto firmado: '+asset.name)
        validate_publication_files(tag,target,channel,paths,gate)
        require_publication_checkout(ROOT,target,channel,lts_base)
        self.require_repository(allow_public);base='/repos/'+self.repository
        if not prerelease:
            from signallab_pc.release_policy import publication_version
            latest = self.api('GET', base+'/releases/latest')
            active = latest.get('tag_name')
            if (latest.get('prerelease') is not False or latest.get('draft') is not False or active != lts_base
                    or publication_version(tag[1:], 'stable') <= publication_version(active[1:], 'stable')):
                raise ValueError('La entrega LTS debe avanzar desde la última estable publicada.')
        try:release=self.api('GET',base+'/releases/tags/'+urllib.parse.quote(tag,safe=''))
        except urllib.error.HTTPError as exc:
            if exc.code!=404:raise
            exc.close()
            release=None
        if release is not None and (release.get('draft') is not True or release.get('prerelease') is not prerelease):
            raise ValueError('La entrega ya publicada o asignada a otro canal se conserva.')
        self.ensure_release_tag(tag,target,title,detached_lts=not prerelease)
        if release is None:
            release=self.api('POST',base+'/releases',{'tag_name':tag,'target_commitish':target,'name':title,'body':notes,'draft':True,'prerelease':prerelease,'make_latest':'false'})
        assets=[self.upload(release,path) for path in paths]
        if {item['name'] for item in self.assets(release)} != {path.name for path in paths}:
            raise ValueError('El borrador tiene adjuntos ajenos a la entrega verificada.')
        release=self.api('PATCH',base+'/releases/'+str(release['id']),{'draft':False,'prerelease':prerelease,'name':title,'body':notes,'make_latest':'false' if prerelease else 'true'})
        print('Release:',release['html_url'],flush=True)
        return release,assets


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag',required=True);parser.add_argument('--title',required=True)
    parser.add_argument('--notes',type=Path,required=True);parser.add_argument('--file',type=Path,action='append',required=True)
    parser.add_argument('--repository',default=REPOSITORY);parser.add_argument('--stable',action='store_true')
    parser.add_argument('--candidate',required=True,help='SHA completo aprobado en la matriz.')
    parser.add_argument('--quality-gate',type=Path,required=True)
    parser.add_argument('--lts-base',help='Última etiqueta LTS publicada, requerida para stable.')
    parser.add_argument('--allow-public',action='store_true',help='Autorizar explícitamente la publicación en el repositorio público configurado.')
    args=parser.parse_args()
    gate = json.loads(args.quality_gate.read_text(encoding='utf-8-sig'))
    GitHub(args.repository).publish(args.tag,args.title,args.notes.read_text(encoding='utf-8'),args.file,
                                   args.candidate,not args.stable,allow_public=args.allow_public,
                                   gate=gate,lts_base=args.lts_base)


if __name__=='__main__':main()
