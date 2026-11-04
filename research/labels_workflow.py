"""Durable sequential annotation benchmark; preserve and restore local services."""
import ctypes
import socket
import subprocess
import sys
import urllib.request
from research.labels_common import *

def state(stage,**extra):
    save(CACHE/'workflow.json',dict(stage=stage,pid=os.getpid(),utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**extra))
    print('OCR_LABEL_WORKFLOW',stage,flush=True)

def command(stage,args,expected=None):
    if expected and expected.exists():return
    folder=CACHE/'logs';folder.mkdir(parents=True,exist_ok=True);log=folder/(stage+'_'+str(time.time_ns())+'.log')
    env=os.environ.copy();env.update(PYTHONIOENCODING='utf-8',PYTORCH_CUDA_ALLOC_CONF='garbage_collection_threshold:0.6')
    with log.open('w',encoding='utf-8',newline='\n') as stream:
        child=subprocess.Popen([sys.executable,*args],cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,
                               creationflags=subprocess.CREATE_NO_WINDOW)
        state(stage,child_pid=child.pid,log=log.relative_to(ROOT).as_posix());code=child.wait()
    if code:raise RuntimeError(stage+' failed; retained '+log.relative_to(ROOT).as_posix())

def port_used(port):
    with socket.socket() as s:return s.connect_ex(('127.0.0.1',port))==0

def health(port):
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(f'http://127.0.0.1:{port}/api/health',timeout=5) as r:return json.load(r)

def start_service(port,app,record_name):
    log=CACHE/(record_name+'.log')
    args=[sys.executable]
    if port==8003:args+=['-m','research.vlm_setup','run','--']
    args+=['-m','uvicorn',app,'--host','127.0.0.1','--port',str(port),'--no-access-log']
    with log.open('a',encoding='utf-8') as stream:
        child=subprocess.Popen(args,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    save(CACHE/(record_name+'.json'),dict(pid=child.pid,port=port,app=app,model_promoted=False))

def start_annotation_web():
    if port_used(8005):
        if health(8005).get('app_id')!='ocr_labels_v1':raise ValueError('Port8005 belongs to another service')
        return
    start_service(8005,'research.labels_web:app','annotation_web')

def pause_source_web():
    if not port_used(8003):return
    if health(8003).get('app_id')!='source_visibility_v3':raise ValueError('Different service on8003; none stopped')
    try:import psutil
    except ModuleNotFoundError:
        from research.vlm_setup import CACHE as runtime
        sys.path.insert(0,str(runtime/'site'))
        try:import psutil
        finally:sys.path.pop(0)
    owners={c.pid for c in psutil.net_connections(kind='tcp') if c.status=='LISTEN' and c.laddr.port==8003}
    if len(owners)!=1 or None in owners:raise ValueError('Cannot identify own research service')
    process=psutil.Process(owners.pop());args=process.cmdline()
    if 'uvicorn' not in args or 'research.v3_web:app' not in args:raise ValueError('Unexpected8003 process; none stopped')
    save(CACHE/'source_web_pause.json',dict(pid=process.pid,reason='Release only existing SourceV3 GPU model for fixed benchmark'))
    process.terminate();process.wait(timeout=15)

def restore_source_web():
    if port_used(8003):return
    start_service(8003,'research.v3_web:app','restored_source_web')

def main():
    import msvcrt
    CACHE.mkdir(parents=True,exist_ok=True)
    with (CACHE/'workflow.lock').open('a+b') as lock:
        if lock.tell()==0:lock.write(b'0');lock.flush()
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
        try:
            freeze_previous()
            if not (OUT/'data_audit.json').exists():raise ValueError('Finish existing preparation/data audit worker before starting supervisor')
            command('publish_prepare',['-m','research.labels_publish','prepare'],OUT/'prepare_publication.json')
            if read(OUT/'prepare_publication.json')['signature']!=signature():raise ValueError('Registered core changed')
            start_annotation_web();pause_source_web()
            for model in ('rapid_v4','rapid_latin_v5'):
                command('main_'+model,['-m','research.labels_study','run','--model',model],OUT/f'evaluation_{model}.json')
            gpu=['-m','research.vlm_setup','run','--','-m','research.labels_study']
            command('main_partial_42',gpu+['run','--model','partial_42'],OUT/'evaluation_partial_42.json')
            for model in ('rapid_v4','rapid_latin_v5','partial_42'):
                prefix=gpu if model=='partial_42' else ['-m','research.labels_study']
                command('fresh_'+model,prefix+['fresh','--model',model],OUT/f'fresh_{model}.json')
            command('scores_audit',['-m','research.labels_audit','scores'],OUT/'audit.json')
            for mode in ('annotations','verified'):
                command('export_'+mode,['-m','research.labels_export','--mode',mode])
            restore_source_web()
            command('software_verification',['-m','research.labels_verify'],OUT/'software_verification.json')
            command('report',['-m','research.labels_report'],ROOT/'research/OCR_LABELS_RESULTS_VI.md')
            command('publish_final',['-m','research.labels_publish','final'])
            state('complete',automated_work_completed=True,human_legibility_verified=False,
                  annotation_url='http://127.0.0.1:8005/',model_promoted=False)
        except Exception as exc:
            state('failed',error_type=type(exc).__name__,detail=str(exc));raise
        finally:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
            restore_source_web()

if __name__=='__main__':main()
