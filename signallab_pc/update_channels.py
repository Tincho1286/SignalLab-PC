"""Discover previews publicly; only a matching signed manifest can select an installer."""
from dataclasses import replace
import http.client
import time
import urllib.request
from .update_manifest import REPOSITORY,FEED_URL,UpdateError,version_tuple,strict_json
from .update_download import _fetch_manifest,checkpoint,Cancelled

PER_PAGE=30
MAX_METADATA=8*1024**2
API=f'https://api.github.com/repos/{REPOSITORY}/releases'


def page_url(page):return API+f'?per_page={PER_PAGE}&page={page}'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


def open_metadata(url):
    from . import __version__
    if not url.startswith(API+'?per_page=30&page=') or not url.removeprefix(API+'?per_page=30&page=').isdecimal():
        raise UpdateError('Dirección del catálogo de versiones no permitida.')
    request=urllib.request.Request(url,headers={'User-Agent':'SignalLab-PC/'+__version__,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
    return urllib.request.build_opener(NoRedirect()).open(request,timeout=15)


def read_page(url,opener,cancel,deadline):
    checkpoint(cancel);raw=bytearray()
    if time.monotonic()>=deadline:raise UpdateError('La consulta de preliminares tardó demasiado.')
    with opener(url) as response:
        if response.geturl()!=url:raise UpdateError('El catálogo redirigió a una dirección inesperada.')
        reader=getattr(response,'read1',response.read)
        while True:
            checkpoint(cancel)
            if time.monotonic()>=deadline:raise UpdateError('La consulta de preliminares tardó demasiado.')
            block=reader(min(8192,MAX_METADATA-len(raw)+1))
            if not block:break
            raw.extend(block)
            if len(raw)>MAX_METADATA:raise UpdateError('El catálogo de versiones excede el tamaño permitido.')
    values=strict_json(bytes(raw))
    if not isinstance(values,list):raise UpdateError('GitHub no devolvió una lista de versiones.')
    return values


def fetch_including_previews(*,cancel,opener,key,now,target=None,metadata_opener=None):
    deadline=time.monotonic()+60;best=None;stable_error=None;notices=[];candidates=set();unsigned=False
    try:best=_fetch_manifest(FEED_URL,cancel=cancel,opener=opener,key=key,now=now,deadline=deadline)
    except Cancelled:raise
    except UpdateError as exc:stable_error=exc
    try:
        page=1
        while True:
            rows=read_page(page_url(page),metadata_opener or open_metadata,cancel,deadline)
            for row in rows:
                if not isinstance(row,dict) or row.get('draft') is not False or row.get('prerelease') is not True:continue
                tag=row.get('tag_name')
                if not isinstance(tag,str) or not tag.startswith('v'):continue
                version=tag[1:]
                try:version_tuple(version)
                except UpdateError:continue
                if best is not None and not version_tuple(version)>version_tuple(best.version):continue
                assets=row.get('assets',[])
                if not isinstance(assets,list):continue
                if not any(isinstance(a,dict) and a.get('name')=='SignalLab-updates.json' and a.get('state','uploaded')=='uploaded' for a in assets):
                    unsigned=True;continue
                candidates.add(version)
            if len(rows)<PER_PAGE:break
            page+=1
        for version in sorted(candidates,key=version_tuple,reverse=True):
            checkpoint(cancel)
            try:
                url=f'https://github.com/{REPOSITORY}/releases/download/v{version}/SignalLab-updates.json'
                candidate=_fetch_manifest(url,cancel=cancel,opener=opener,key=key,now=now,expected_channel='preview',expected_version=version,deadline=deadline)
                if target is not None and target not in candidate.assets:
                    notices.append('La preliminar '+version+' todavía no tiene instalador para este equipo.');continue
                best=candidate;break
            except Cancelled:raise
            except UpdateError:notices.append('La preliminar '+version+' no tiene un manifiesto válido y no se ofrece para instalar.')
    except Cancelled:raise
    except (UpdateError,OSError,TimeoutError,http.client.HTTPException):
        notices.append('No se pudo completar la consulta de preliminares. Se conserva la versión firmada que pudo verificarse.')
    if best is None:raise stable_error or UpdateError('No hay una versión compatible con un manifiesto firmado válido.')
    if unsigned:notices.append('Las preliminares sin manifiesto firmado compatible quedan fuera de la actualización automática.')
    return replace(best,notices=tuple(dict.fromkeys(notices)))
