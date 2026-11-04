"""Generate Windows resource metadata without importing application code."""
from pathlib import Path
import argparse,ast,json,re

def version_metadata(filename=None):
    root=Path(__file__).resolve().parents[1]
    tree=ast.parse((root/'signallab_pc/__init__.py').read_text(encoding='utf-8'))
    value=next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='__version__' for target in node.targets))
    match=re.fullmatch(r'(\d+)\.(\d+)\.(\d+)(?:[.+-]([A-Za-z0-9.-]+))?',value)
    if not match:raise ValueError('The application version must have three numeric components.')
    numeric=tuple(int(match.group(i)) for i in (1,2,3))+(0,)
    if any(part>65535 for part in numeric):raise ValueError('The Windows version exceeds its four-word representation.')
    if filename is None:filename='SignalLab-PC-'+value+'.exe'
    if not re.fullmatch(r'SignalLab-PC-[A-Za-z0-9._-]+\.exe',filename):raise ValueError('Unexpected portable filename.')
    fields={'CompanyName':'SignalLab PC contributors','FileDescription':'SignalLab PC - Signals and Systems Laboratory','FileVersion':'.'.join(map(str,numeric)),'InternalName':'SignalLab PC','LegalCopyright':'Copyright (C) 2026 SignalLab PC contributors','OriginalFilename':filename,'ProductName':'SignalLab PC','ProductVersion':value}
    strings=',\n'.join('StringStruct('+repr(key)+', '+repr(text)+')' for key,text in fields.items())
    resource='VSVersionInfo(ffi=FixedFileInfo(filevers='+repr(numeric)+', prodvers='+repr(numeric)+', mask=0x3f, flags='+('0x2' if match.group(4) else '0x0')+', OS=0x40004, fileType=0x1, subtype=0x0, date=(0,0)), kids=[StringFileInfo([StringTable("040904B0", ['+strings+'])]), VarFileInfo([VarStruct("Translation", [1033,1200])])])\n'
    return resource,{'version':value,'file_version':fields['FileVersion'],'filename':filename,'product_name':fields['ProductName']}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--filename');parser.add_argument('--output',type=Path,required=True);parser.add_argument('--metadata-output',type=Path,required=True)
    args=parser.parse_args();resource,details=version_metadata(args.filename)
    for path,text in ((args.output,resource),(args.metadata_output,json.dumps(details,indent=2)+'\n')):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8',newline='\n')

if __name__=='__main__':main()
