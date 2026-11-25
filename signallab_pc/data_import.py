"""One typed file loader for local inputs and the result picker."""
from pathlib import Path
from PySide6.QtWidgets import QFileDialog,QInputDialog
from .resources import ensure_working_set


SIGNAL_FILES='Señales y resultados (*.json *.csv *.tsv *.mat *.m)'


def load_signal(parent,kind='discrete',path=None):
    if path is None:path,_=QFileDialog.getOpenFileName(parent,'Importar datos de entrada','',SIGNAL_FILES)
    if not path:return None
    path=Path(path);ensure_working_set(path.stat().st_size,bytes_per_sample=1,live_arrays=8)
    if path.suffix.lower() in ('.csv','.tsv'):
        from .storage import load_csv
        with path.open(encoding='utf-8-sig') as stream:own=stream.readline(100).startswith('# SignalLab CSV v1')
        if own:return load_csv(path)
        from .csv_import_dialog import CsvImportDialog
        dialog=CsvImportDialog(str(path),kind,parent)
        return dialog.result_signal if dialog.exec() else None
    if path.suffix.lower() in ('.mat','.m'):
        from .matlab_import_dialog import MatlabImportDialog
        dialog=MatlabImportDialog(str(path),kind,parent)
        return dialog.result_signal if dialog.exec() else None
    from .storage import load_json
    return load_json(path)


def load_results(parent,kind,constraints):
    """Stage and validate before adding compatible objects to the current project."""
    from .project import Project
    from .reuse_sources import source_info,compatible
    from .model import Signal
    from .filters import Transfer
    path,_=QFileDialog.getOpenFileName(parent,'Importar archivo compatible','',SIGNAL_FILES if kind in ('signal','cas_source') else 'Resultados o expresiones SignalLab (*.json)')
    if not path:return None
    path=Path(path);staged=Project()
    if kind in ('signal','cas_source') and path.suffix.lower()!='.json':
        domains=constraints.get('domains');domain=domains[0] if domains and len(domains)==1 else 'import'
        value=load_signal(parent,domain,str(path))
        if value is None:return None
        staged.add(value,operation='Importación de '+path.name)
    else:
        from .input_files import read_json
        document=read_json(path,live_arrays=10)
        if not isinstance(document,dict):raise ValueError('El JSON debe contener un objeto SignalLab.')
        format_=document.get('format')
        if format_=='signallab-project':staged=Project.from_document(document)
        elif format_=='signallab-signal':
            from .storage import signal_from_document
            staged.add(signal_from_document(document),operation='Importación de señal JSON')
        elif format_=='signallab-transfer':staged.add(Transfer.from_document(document),operation='Importación de sistema JSON')
        elif 'request' in document and 'result' in document:
            staged.add(document,title=path.stem,operation='Importación de expresión')
        else:raise ValueError('Formato no compatible. Usá JSON de señal, sistema, expresión o selección exportada de Resultados.')
    candidates=[]
    for record in staged.headers():
        if compatible(source_info(staged,record['id'],kind),**constraints):candidates.append(record)
    if not candidates:raise ValueError('El archivo no contiene datos compatibles con el dominio, variable y unidades de esta entrada.')
    if len(candidates)>1:
        labels=[str(i+1)+'. '+r['title']+' · '+r['operation'] for i,r in enumerate(candidates)]
        selection,ok=QInputDialog.getItem(parent,'Datos del archivo','Elegí qué resultado importar',labels,len(labels)-1,False)
        if not ok:return None
        chosen=candidates[labels.index(selection)]
    else:chosen=candidates[0]
    window=parent.parentWidget()
    mapping = window.project.incorporate(staged, root=chosen['id'], operation_prefix='Archivo '+path.name+' · ')
    window.refresh_project()
    return mapping[chosen['id']]
