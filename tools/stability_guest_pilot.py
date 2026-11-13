"""Register a single, non-repeating calibration on a current AI member."""
import json
import sys
import time
from stability_guest import membership
from stability_stats import connect, master

def main(name):
    if name not in membership():
        raise SystemExit('Requested node is not in the current AI group')
    with connect(master(), True) as db:
        run=db.execute("select id,end,state,phase from st_run order by id desc limit 1").fetchone()
        if run['phase']!='formal' or run['state']!='running' or run['end']<=time.time():
            raise SystemExit('No current formal run')
        rows=db.execute("select distinct n.id from st_active a join st_node n on n.id=a.node where a.run=? and a.end is null and n.name=?",(run['id'],name)).fetchall()
        if len(rows)!=1:
            raise SystemExit('No unique active node')
        data=dict(node=rows[0][0],name=name,timeout_s=27,passive_challenge_observation_s=8,
                  max_visits=1,target='https://chatgpt.com/')
        db.execute("insert into st_event values(?,?,?,?)",(run['id'],time.time(),'CHATGPT_PILOT_REQUEST',json.dumps(data)))
        print('Registered one calibration:',name)

if __name__=='__main__':
    main(sys.argv[1])
