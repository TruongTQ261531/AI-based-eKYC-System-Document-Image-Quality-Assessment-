"""Read-only progress command. Does not start training, load models or change state."""
from research.v2_common import CACHE,OUT,read

def main():
    for name in ('workflow','completion','progress'):
        path=CACHE/(name+'.json')
        if not path.exists():continue
        r=read(path)
        print(name+': '+str(r.get('stage','unknown'))+' | UTC '+str(r.get('time_utc','')))
        if 'step' in r:print('  optimizer step '+str(r['step'])+'/320 | seed '+str(r.get('seed','')))
        if 'complete' in r:print('  complete '+str(r['complete'])+'/'+str(r.get('total','')))
        if 'failure' in r or 'detail' in r:print('  Failure recorded. Inspect local workflow log; no result is invented.')
    print('test seal published: '+str((OUT/'lock_publication.json').exists()))
    print('audit passed: '+str((OUT/'audit.json').exists() and read(OUT/'audit.json').get('status')=='passed'))

if __name__=='__main__':main()
