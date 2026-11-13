"""Arm one guest window on the existing formal run. Repeating is idempotent."""
import json
import time
from stability_stats import connect,master
from stability_guest import CONDITIONS,SCHEMA,membership

def arm():
    names=membership()
    if not names:
        raise RuntimeError('AI group is empty')
    with connect(master(),True) as db:
        db.executescript(SCHEMA)
        db.execute('begin immediate')
        r=db.execute("select id,end,state,phase from st_run order by id desc limit 1").fetchone()
        now=time.time()
        if r['state']!='running' or r['phase']!='formal' or now>=r['end']:
            raise RuntimeError('no active formal run')
        old=db.execute('select at,data from st_event where run=? and kind=?',(r['id'],CONDITIONS)).fetchone()
        if old:
            print('Existing guest window',old[0],json.loads(old[1])['end'])
            return
        end=min(now+1800,r['end'])
        data=dict(end=end,ai_names=names,group='Jimmy · ai',scope='anonymous-rendered-visitor',
                  retained_probe_bytes=8192,minimum_start_spacing_s=30,timeout_s=27,
                  browser_download_KiBps=256,browser_upload_KiBps=64,max_browsers=1,
                  group_by=['provider','name'],inventory='match installed per node name despite generation drift',
                  ok='official 200 + anonymous backend response + loaded editable composer for four seconds',
                  ng='explicit region denial; challenges and timeouts indeterminate')
        db.execute('insert into st_event values(?,?,?,?)',(r['id'],now,CONDITIONS,json.dumps(data,ensure_ascii=False)))
        print('armed',r['id'],len(names),now,end)

if __name__=='__main__':
    arm()
