"""Record measured-machine/software context without exporting environment secrets."""
import ctypes
import importlib.metadata
import os
import platform
import sys
import time

from research.benchmark import save,digest
from research.recovery_study import OUT


def main():
    cpu=platform.processor();ram=None
    if os.name=='nt':
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
            cpu=winreg.QueryValueEx(key,'ProcessorNameString')[0].strip()
        class Memory(ctypes.Structure):
            _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in
                ('total_physical','available_physical','total_pagefile','available_pagefile','total_virtual','available_virtual','extended')]
        memory=Memory();memory.length=ctypes.sizeof(Memory)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):ram=memory.total_physical
    versions={}
    for name in ('numpy','scipy','opencv-python','opencv-python-headless','opencv-contrib-python','Pillow','onnxruntime','torch','torchvision','easyocr','vietocr',
                 'shapely','pyclipper','fastapi','starlette','uvicorn','httpx','pytest','anyio'):
        try:versions[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:versions[name]=None
    save(OUT/'environment.json',dict(time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        cpu=cpu,logical_processors=os.cpu_count(),ram_bytes=ram,platform=platform.platform(),python=platform.python_version(),
        executable=sys.executable,versions=versions,execution_provider='CPUExecutionProvider',
        per_session_intraop_threads=2,opencv_threads=1,desktop_cpu_not_exclusively_reserved=True,
        rapidocr='1.4.4 official wheel imported from verified private cache; not installed',code_sha256=digest(__file__)))
    print('ENVIRONMENT_RECORDED',cpu,flush=True)


if __name__=='__main__':main()
