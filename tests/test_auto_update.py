"""Publication regressions against temporary bare remotes; no public network."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import auto_update as a
import maintain as m

def run(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.DEVNULL).decode().strip()
def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(data,encoding='utf-8',newline='\n')

class AutoPublicationChecks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base=Path(self.temp.name);self.remote=base/'remote.git';self.root=base/'work'
        subprocess.run(['git','init','--bare',str(self.remote)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.root.mkdir();run(self.root,'init','-b','main')
        run(self.root,'config','user.name','Synthetic test');run(self.root,'config','user.email','test@example.invalid')
        run(self.root,'config','commit.gpgsign','false');run(self.root,'config','core.autocrlf','false')
        write(self.root/'.gitignore','.local/\n')
        write(self.root/'PROGRESS.md','# Current\n<!-- sop-current-end -->\nHISTORY\n')
        write(self.root/'rules/vendor/ads-expanded.yaml','payload:\n- DOMAIN,old.example.invalid\n')
        write(self.root/'research/sources.lock.json',json.dumps({'resources':[{'output':'rules/vendor/ads-expanded.yaml'}]}))
        run(self.root,'add','--','.gitignore','PROGRESS.md','rules/vendor/ads-expanded.yaml','research/sources.lock.json')
        run(self.root,'commit','-m','Synthetic baseline')
        run(self.root,'remote','add','origin',str(self.remote));run(self.root,'push','-u','origin','main')
        self.original=run(self.root,'rev-parse','HEAD')
    def report(self,root):
        return {'schema':1,'checked_at_utc':'2026-10-28T00:00:00Z','operation':'check',
                'ok':True,'repositories':{m.PRIMARY:{'head':'1'*40,'status':'ok'}},
                'files':[],'summary':{k:(1 if k=='review-required' else 0) for k in m.STATUS}}
    def update(self,root,report):
        file='rules/vendor/ads-expanded.yaml'
        write(root/file,'payload:\n- DOMAIN,new.example.invalid\n')
        identifier='20261028T000000Z-11111111'
        (root/'.local/maintenance/backups'/identifier).mkdir(parents=True)
        m.write_json(root/'.local/maintenance/backups'/identifier/'manifest.json',
                     {'files':[{'path':file,'after_sha256':a.digest(root/file)}]})
        return identifier
    def execute(self,updater=None):
        return a.execute(self.root,expected_origin=str(self.remote),checker=self.report,updater=updater or self.update)
    def test_noop_creates_no_commit_or_push_even_when_review_is_pending(self):
        with mock.patch.object(a,'push') as push:
            result=self.execute(lambda *_:None)
        self.assertEqual(result['status'],'no_relevant_changes')
        push.assert_not_called();self.assertEqual(run(self.root,'rev-parse','HEAD'),self.original)
        self.assertFalse((self.root/a.EVIDENCE).exists())
    def test_changed_verified_rules_commit_only_expected_files_and_push(self):
        result=self.execute()
        self.assertTrue(result['pushed'])
        self.assertEqual(run(self.root,'rev-parse','HEAD'),run(self.remote,'rev-parse','refs/heads/main'))
        self.assertEqual(set(result['files']),{'rules/vendor/ads-expanded.yaml','PROGRESS.md',a.EVIDENCE})
        self.assertEqual(run(self.root,'status','--porcelain'),'')
        self.assertTrue((self.root/'PROGRESS.md').read_bytes().endswith(b'HISTORY\n'))
    def test_dirty_or_staged_user_work_stops_before_updater(self):
        write(self.root/'user.txt','USER CONTENT')
        with self.assertRaises(m.MaintenanceError):self.execute()
        self.assertEqual(run(self.root,'rev-parse','HEAD'),self.original)
        self.assertEqual((self.root/'user.txt').read_text(),'USER CONTENT')
        run(self.root,'add','user.txt')
        with self.assertRaises(m.MaintenanceError):self.execute()
    def test_unrelated_changes_during_update_are_never_committed(self):
        def raced(root,report):
            identifier=self.update(root,report);write(root/'user.txt','PRESERVE');return identifier
        with self.assertRaises(m.MaintenanceError):self.execute(raced)
        self.assertEqual(run(self.root,'rev-parse','HEAD'),self.original)
        self.assertEqual((self.root/'user.txt').read_text(),'PRESERVE')
    def test_unknown_ahead_commits_are_not_pushed(self):
        run(self.root,'commit','--allow-empty','-m','User unpublished work')
        with self.assertRaises(m.MaintenanceError):self.execute()
        self.assertEqual(run(self.remote,'rev-parse','refs/heads/main'),self.original)
    def test_failed_push_retries_only_own_recorded_commit(self):
        original=a.git
        def failed(root,*args):
            if args[0]=='push':raise m.MaintenanceError('synthetic_network_failure')
            return original(root,*args)
        with mock.patch.object(a,'git',side_effect=failed):
            with self.assertRaises(m.MaintenanceError):self.execute()
        pending=run(self.root,'rev-parse','HEAD')
        self.assertNotEqual(pending,self.original)
        result=self.execute()
        self.assertEqual(result['status'],'retried_publication')
        self.assertEqual(run(self.remote,'rev-parse','refs/heads/main'),pending)
    def test_remote_change_after_check_is_not_overwritten(self):
        original=a.push
        def changed(root,journal):
            run(root,'update-ref','refs/remotes/origin/main','HEAD')
            return original(root,journal)
        # An unexpected remote tracking value is rejected without force push.
        with mock.patch.object(a,'push',side_effect=changed):
            with self.assertRaises(m.MaintenanceError):self.execute()
        self.assertEqual(run(self.remote,'rev-parse','refs/heads/main'),self.original)
    def test_push_received_but_confirmation_failed_is_not_pushed_twice(self):
        original=a.git
        def failed_confirmation(root,*args):
            if args[0]=='ls-remote':raise m.MaintenanceError('synthetic_confirmation_failure')
            return original(root,*args)
        with mock.patch.object(a,'git',side_effect=failed_confirmation):
            with self.assertRaises(m.MaintenanceError):self.execute()
        received=run(self.remote,'rev-parse','refs/heads/main')
        with mock.patch.object(a,'push') as push:
            result=self.execute()
        push.assert_not_called()
        self.assertEqual(result['status'],'publication_already_received')
        self.assertEqual(run(self.root,'rev-parse','HEAD'),received)
    def test_wrong_origin_or_branch_is_rejected(self):
        with self.assertRaises(m.MaintenanceError):
            a.execute(self.root,checker=self.report,updater=self.update)
        run(self.root,'checkout','-b','other')
        with self.assertRaises(m.MaintenanceError):self.execute()

if __name__=='__main__':unittest.main()
