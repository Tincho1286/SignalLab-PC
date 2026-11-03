"""Publish SignalLab releases with an explicit public-repository opt-in using Git's existing GitHub session."""
from pathlib import Path
import argparse,hashlib,http.client,json,os,subprocess,urllib.request,urllib.error,urllib.parse

REPOSITORY='Tincho1286/SignalLab-PC'


def sha256(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024**2),b''):digest.update(block)
    return digest.hexdigest()


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

    def ensure_release_tag(self,tag,target,title):
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
        timestamp=parsedate_to_datetime(server_date).astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        maintainer=self.api('GET','/user')
        annotated=self.api('POST',base+'/git/tags',{'tag':tag,'message':title+'\n\nBuild source commit: '+target+'.','object':target,'type':'commit','tagger':{'name':maintainer['login'],'email':str(maintainer['id'])+'+'+maintainer['login']+'@users.noreply.github.com','date':timestamp}})
        self.api('POST',base+'/git/refs',{'ref':'refs/tags/'+tag,'sha':annotated['sha']})

    def publish(self,tag,title,notes,paths,target,prerelease=True,allow_public=False):
        self.require_repository(allow_public);base='/repos/'+self.repository
        self.ensure_release_tag(tag,target,title)
        try:release=self.api('GET',base+'/releases/tags/'+urllib.parse.quote(tag,safe=''))
        except urllib.error.HTTPError as exc:
            if exc.code!=404:raise
            release=self.api('POST',base+'/releases',{'tag_name':tag,'target_commitish':target,'name':title,'body':notes,'draft':True,'prerelease':prerelease})
        assets=[self.upload(release,path) for path in paths]
        release=self.api('PATCH',base+'/releases/'+str(release['id']),{'draft':False,'prerelease':prerelease,'name':title,'body':notes})
        print('Release:',release['html_url'],flush=True)
        return release,assets


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag',required=True);parser.add_argument('--title',required=True)
    parser.add_argument('--notes',type=Path,required=True);parser.add_argument('--file',type=Path,action='append',required=True)
    parser.add_argument('--repository',default=REPOSITORY);parser.add_argument('--stable',action='store_true')
    parser.add_argument('--allow-public',action='store_true',help='Autorizar explícitamente la publicación en el repositorio público configurado.')
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    if subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=root).returncode:raise SystemExit('Guardá los cambios en Git antes de publicar.')
    target=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=root,text=True).split()
    if not remote or remote[0]!=target:raise SystemExit('Subí el commit a origin/main antes de publicar.')
    GitHub(args.repository).publish(args.tag,args.title,args.notes.read_text(encoding='utf-8'),args.file,target,not args.stable,allow_public=args.allow_public)


if __name__=='__main__':main()
