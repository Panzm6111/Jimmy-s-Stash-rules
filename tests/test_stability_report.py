import json
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from stability import capture_quality,final_audit
from stability_chatgpt import SCHEMA
from stability_stats import aggregate,connect
from stability_view import report,rankings,streaks


class Reports(unittest.TestCase):
    def test_capture_is_independent_of_attribution_and_rejects_overlap(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'db'
            path.touch()
            db=connect(path,True)
            try:
                db.executescript(SCHEMA)
                db.execute('insert into st_active values(1,1,100,110)')
                sql="""insert into st_sample(run,node,slot,start,end,target,elapsed,delay,status,raw,interval)
                       values(1,1,?,?,?,0,3000,null,'UNKNOWN_ERROR','NODE_TIMEOUT/504',5)"""
                db.executemany(sql,[(100,100,103),(105,105,108)])
                r={'id':1,'end':110}
                self.assertEqual(capture_quality(db,r),dict(min_captured_time_coverage=1,overlaps=0,actual_peak=1))
                db.execute("insert into st_chatgpt(run,node,slot,start,end,status) values(1,1,101,101,102,'TIMEOUT')")
                self.assertEqual(capture_quality(db,r)['overlaps'],1)
                db.execute("update st_sample set raw='API_UNAVAILABLE/controller-transport' where slot=105")
                self.assertEqual(capture_quality(db,r)['min_captured_time_coverage'],.5)
            finally:
                db.close()

    def test_final_window_with_holes(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'master.db'
            path.touch()
            db=connect(path,True)
            try:
                stop=time.time()-1
                start=stop-3*86400
                db.execute("insert into st_run values(1,'formal',?,?,'complete',x'01')",(start,stop))
                db.execute("insert into st_node values(1,'n','p','<script>test</script>','http')")
                db.execute("insert into st_active values(1,1,?,null)",(start,))
                rows=[]
                for i,status in enumerate(['SUCCESS','NODE_TIMEOUT','NODE_TIMEOUT','SKIPPED_BUSY','NODE_TEST_FAILED','SUCCESS']):
                    slot=start+i*5
                    raw=dict(run=1,node=1,slot=slot,start=None if status=='SKIPPED_BUSY' else slot,
                             end=None if status=='SKIPPED_BUSY' else slot+1,target=0,delay=150 if status=='SUCCESS' else None,
                             elapsed=None if status=='SKIPPED_BUSY' else 1000,status=status,raw=status,interval=5,env=1)
                    db.execute('''insert into st_sample(run,node,slot,start,end,target,delay,elapsed,status,raw,interval,env)
                        values(:run,:node,:slot,:start,:end,:target,:delay,:elapsed,:status,:raw,:interval,:env)''',raw)
                    rows.append(raw)
                aggregate(db,1,rows)
                db.commit()
                r=db.execute('select * from st_run').fetchone()
                raw=streaks(db,1,1)[0]
                self.assertEqual(raw[:5],(2,3,2,2,5))
                ranks=rankings(db,r)
                self.assertFalse(any(x['eligible'] for v in ranks.values() for x in v))
                self.assertAlmostEqual(ranks['全部'][0]['request_coverage'],5/(3*86400/5),places=7)
                audit=final_audit(db,r)
                self.assertTrue(audit['calendar_elapsed'] and audit['database_ok'])
                self.assertEqual(audit['eligible_by_band']['全部'],0)
                with patch('stability_view.PRIVATE',Path(d)):
                    rendered=report(db,1).read_text('utf8')
                self.assertIn('建议补测',rendered)
                self.assertIn('逐日有效覆盖不足',rendered)
                self.assertIn('日历窗口结束',rendered)
                self.assertIn('&lt;script&gt;',rendered)
                self.assertNotIn('<script>test</script>',rendered)
            finally:
                db.close()
