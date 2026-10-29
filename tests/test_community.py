"""Maintained-set integrity and compatibility regressions; simulated data only."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import community_rules as c
import maintain as m
import refresh_community as refresh
from scan_secrets import inspect


class MaintainedRules(unittest.TestCase):
    def test_adobe_official_supplement_survives_community_refresh_and_rejects_bad_hosts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'source.yaml').write_text('payload: ["DOMAIN,new.example.invalid"]',encoding='utf-8')
            supplement={'suffixes':['frame.example.invalid'],'exact_hosts':['media.storage.example.invalid']}
            (root/'official.json').write_text(json.dumps(supplement),encoding='utf-8')
            manifest={'resources':[{'id':'vendor','output':'source.yaml'}],
                      'aggregates':[{'output':'adobe.yaml','sources':['vendor'],'official_supplement':'official.json'}]}
            generated=c.generated_documents(root,manifest)['adobe.yaml']
            self.assertIn('DOMAIN,new.example.invalid',generated)
            self.assertIn('DOMAIN-SUFFIX,frame.example.invalid',generated)
            self.assertIn('DOMAIN,media.storage.example.invalid',generated)
            supplement['exact_hosts']=['unsafe.invalid,DIRECT']
            (root/'official.json').write_text(json.dumps(supplement),encoding='utf-8')
            with self.assertRaises(m.MaintenanceError):c.generated_documents(root,manifest)

    def test_domain_conversion_keeps_whole_set_and_exact_semantics(self):
        rules,omitted=c.parse(b'payload:\n - +.example.invalid\n - api.example.invalid\n - api.example.invalid\n','domain_yaml')
        self.assertEqual(rules,['DOMAIN-SUFFIX,example.invalid','DOMAIN,api.example.invalid'])
        self.assertEqual(omitted,[])

    def test_url_regex_is_reported_and_not_weakened_to_domain(self):
        rules,omitted=c.parse(b'# source\nDOMAIN,api.example.invalid\nURL-REGEX,^https://example.invalid/path\n','classical_text')
        self.assertEqual(rules,['DOMAIN,api.example.invalid'])
        self.assertEqual(omitted,['URL-REGEX,^https://example.invalid/path'])

    def test_unknown_rules_actions_empty_and_duplicate_keys_fail(self):
        for raw,fmt in [(b'DOMAIN,a.invalid,DIRECT','classical_text'),
                        (b'MATCH,DIRECT','classical_text'),
                        (b'payload: []','domain_yaml'),
                        (b'payload: [a.invalid]\npayload: [b.invalid]','domain_yaml'),
                        (b'payload: [https://a.invalid/path]','domain_yaml')]:
            with self.subTest(raw=raw),self.assertRaises((ValueError,m.MaintenanceError)):
                c.parse(raw,fmt)

    def test_manifest_hashes_licenses_and_full_aggregates(self):
        c.verify(ROOT)

    def test_generated_branch_and_license_branch_are_tracked_independently(self):
        sources=m.collect_sources(ROOT)
        meta=[x for x in sources if x['repository']=='MetaCubeX/meta-rules-dat']
        self.assertTrue(meta)
        for item in meta:
            self.assertEqual(item['ref'],'refs/heads/master' if 'license' in item['categories'] else 'refs/heads/meta')
        self.assertFalse(any('curated' in x['categories'] for x in sources))

    def test_refresh_rejects_second_download_or_license_change_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'research').mkdir()
            old=b'payload:\n - api.example.invalid\n';license=b'simulated license'
            manifest={'resources':[{'id':'test','repository':'MetaCubeX/meta-rules-dat','path':'test.yaml',
                      'output':'out.yaml','source_format':'domain_yaml','source_sha256':m.sha256(old)}],
                      'aggregates':[],'licenses':[{'repository':'MetaCubeX/meta-rules-dat','path':'LICENSE','sha256':m.sha256(license)}]}
            path=root/c.MANIFEST;path.write_text(json.dumps(manifest),encoding='utf-8')
            report={'files':[{'repository':'MetaCubeX/meta-rules-dat','path':'LICENSE','categories':['license'],'latest_url':'license'},
                             {'repository':'MetaCubeX/meta-rules-dat','path':'test.yaml','outputs':['out.yaml'],'latest_url':'data','latest_sha256':m.sha256(old)}]}
            before=path.read_bytes()
            for payloads in ({'license':license+b'change','data':old},{'license':license,'data':old+b'change'}):
                with self.assertRaises(ValueError):refresh.refresh(root,report,payloads.__getitem__)
                self.assertEqual(path.read_bytes(),before)
                self.assertFalse((root/'out.yaml').exists())

    def test_public_uuid_hostname_does_not_exempt_credentials(self):
        value='12345678-'+'1234-4567-8901-'+'123456789abc'
        self.assertEqual(inspect('- DOMAIN-SUFFIX,'+value+'.example.invalid','fixture'),[])
        for row in ['uuid: '+value,'server: '+value+'.example.invalid','https://'+value+'.example.invalid','note '+value]:
            self.assertTrue(inspect(row,'fixture'),row.split(':')[0])

    def test_public_api_blob_bytes_must_match_git_object_id(self):
        raw=b'public test source';oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        import base64
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,*args):return json.dumps({'sha':'0'*40,'encoding':'base64','content':base64.b64encode(raw).decode()}).encode()
        with mock.patch.object(m.urllib.request,'urlopen',return_value=Response()),mock.patch.object(m,'cache_public') as cache:
            with self.assertRaises(m.MaintenanceError):
                m.fetch_public_api(m.source_url('MetaCubeX/meta-rules-dat',oid,'test.yaml'))
            cache.assert_not_called()

    def test_community_increment_uses_checked_ref_and_reversible_transaction(self):
        from test_maintenance import SourceFixture,public_url,git,write_json,OLD_REVISION,NEW_REVISION
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'repo';root.mkdir()
            git(root,'init','-q');git(root,'config','user.name','Simulation')
            git(root,'config','user.email','simulation@example.invalid')
            git(root,'config','commit.gpgsign','false');git(root,'config','core.autocrlf','false')
            hooks=root/'.git/empty-hooks';hooks.mkdir();git(root,'config','core.hooksPath',str(hooks))
            (root/'.gitignore').write_text('.local/\n',encoding='utf-8')
            f=SourceFixture(root)
            output=root/'rules/vendor/ads-expanded.yaml';output.parent.mkdir(parents=True)
            output.write_bytes(f.rule_bytes)
            repo='MetaCubeX/meta-rules-dat';source='geo/geosite/fixture.yaml'
            raw=b'payload:\n'+b''.join(f' - api{i}.example.invalid\n'.encode() for i in range(10))
            new=raw+b' - added.example.invalid\n';lic=b'simulated meta license'
            for revision in [OLD_REVISION,NEW_REVISION]:
                f.data[public_url(repo,revision,source)]=raw if revision==OLD_REVISION else new
                f.data[public_url(repo,revision,'LICENSE')]=lic
            (root/'licenses/meta.txt').write_bytes(lic)
            body=c.document(c.parse(raw,'domain_yaml')[0],['fixture'])
            part='rules/vendor/fixture-community.yaml';(root/part).write_text(body,encoding='utf-8',newline='\n')
            manifest={'resources':[{'id':'fixture','repository':repo,'path':source,'revision':OLD_REVISION,
                       'ref':'refs/heads/meta','url':public_url(repo,OLD_REVISION,source),'source_format':'domain_yaml',
                       'source_sha256':m.sha256(raw),'output':part,'output_sha256':m.sha256(body.encode())}],
                      'licenses':[{'repository':repo,'path':'LICENSE','ref':'refs/heads/master','url':public_url(repo,OLD_REVISION,'LICENSE'),
                       'file':'licenses/meta.txt','sha256':m.sha256(lic)}],
                      'aggregates':[{'output':'rules/openai.yaml','sources':['fixture']}]}
            write_json(root/c.MANIFEST,manifest)
            for path,text in c.generated_documents(root,manifest).items():(root/path).write_text(text,encoding='utf-8',newline='\n')
            git(root,'add','.');git(root,'commit','-qm','Simulated community baseline')
            head=git(root,'rev-parse','HEAD');before=(root/part).read_bytes()
            report=m.check_upstreams(root,fetcher=f.fetch,head_resolver=lambda *args:NEW_REVISION)
            self.assertTrue(report['ok']);self.assertEqual(report['summary']['rules-update'],1)
            real_run=m.run_step;steps=[]
            def run(directory,command,label,timeout=240):
                steps.append(label)
                if label=='clone':return real_run(directory,command,label,timeout)
                if label=='refresh_community':refresh.refresh(directory,report,f.fetch)
            with mock.patch.object(m.shutil,'which',return_value='node'),mock.patch.object(m,'run_step',side_effect=run):
                backup=m.update(root,report)
            self.assertIn('project_and_scripts',steps)
            self.assertNotIn('refresh_rules',steps)
            self.assertEqual(len(m.rule_payload((root/part).read_bytes())),11)
            self.assertEqual(git(root,'rev-parse','HEAD'),head)
            m.rollback(root,backup)
            self.assertEqual((root/part).read_bytes(),before)
            self.assertEqual(git(root,'status','--porcelain'),'')


if __name__=='__main__':unittest.main()
