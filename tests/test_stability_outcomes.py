"""Ensure fault attribution cannot erase observed request failures."""
import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from stability_outcomes import outcome,summarize


class Outcomes(unittest.TestCase):
    def test_attribution_does_not_change_observed_outcome(self):
        for status in ('NODE_TIMEOUT','UNKNOWN_ERROR','LOCAL_NETWORK_DOWN','TARGET_UNAVAILABLE'):
            self.assertEqual(outcome(status,'NODE_TIMEOUT/504',True,True),'TIMEOUT')
        self.assertEqual(outcome('UNKNOWN_ERROR','NODE_TEST_FAILED/503',True,True),'PROBE_FAILED')

    def test_no_guessing_from_positive_delay_or_unfinished_intent(self):
        self.assertEqual(outcome('UNKNOWN_ERROR','UNKNOWN_ERROR/204-not-confirmed',True,True,True),'RESPONSE_UNCONFIRMED')
        self.assertEqual(outcome('SUCCESS','SUCCESS/200/204',True,True,False),'UNRESOLVED')
        self.assertEqual(outcome('UNKNOWN_ERROR','crash-after-admission',True,False),'INTERRUPTED')
        self.assertEqual(outcome('PENDING',None,True,False),'IN_PROGRESS')
        self.assertEqual(outcome('SKIPPED_BUSY','SKIPPED_BUSY',False,False),'NOT_STARTED')

    def test_reclassifying_cause_changes_neither_rate_nor_source_rows(self):
        db=sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.execute('create table st_sample(run,node,status,raw,start,end,elapsed,delay,interval)')
        db.executemany('insert into st_sample values(1,1,?,?,?,?,?,?,5)',[
            ('SUCCESS','SUCCESS/200/204',1,2,1000,100),
            ('UNKNOWN_ERROR','NODE_TIMEOUT/504',3,6,3000,None),
            ('NODE_TEST_FAILED','NODE_TEST_FAILED/503',8,9,1000,None),
            ('UNKNOWN_ERROR','crash-after-admission',10,None,None,None),
            ('SKIPPED_BUSY','SKIPPED_BUSY',None,None,None,None)])
        before=list(db.execute('select * from st_sample'))
        a=summarize(db,1)[None]
        self.assertEqual(a['known'],3)
        self.assertAlmostEqual(a['request_success_pct'],100/3)
        self.assertEqual(a['outcome_unknown'],1)
        self.assertEqual(a['known_failure_with_uncertain_cause'],1)
        self.assertEqual(list(db.execute('select * from st_sample')),before)
        db.execute("update st_sample set status='NODE_TIMEOUT' where raw='NODE_TIMEOUT/504'")
        b=summarize(db,1)[None]
        self.assertEqual(a['request_success_pct'],b['request_success_pct'])
        self.assertEqual(b['known_failure_with_uncertain_cause'],0)
