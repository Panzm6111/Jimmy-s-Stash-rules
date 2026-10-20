const {test} = require('node:test');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const cases = JSON.parse(execFileSync('python3', ['-c', `import json,yaml
from pathlib import Path
print(json.dumps([{"module":p.stem,"rules":yaml.safe_load(p.read_text()).get('http',{}).get('url-rewrite',[])} for p in Path('modules/ads').glob('*.stoverride')]))`], {cwd:root}));
test('native fixed responses preserve source action semantics; no empty-response provider remains', () => {
  const unicom=cases.find(c=>c.module==='unicom');
  assert.equal(unicom.rules.length,2);
  for(const r of unicom.rules) assert.ok(r.endsWith(' - reject-img'));
  for(const c of cases) for(const r of c.rules) assert.match(r, / - reject(?:-200|-dict|-img|-array)?$/);
  const weibo=cases.find(c=>c.module==='weibo');
  assert.equal(weibo.rules.length,2);
  for(const r of weibo.rules) assert.ok(r.endsWith(' - reject-dict'));
});
test('fixed rules never depend on a response object or JS invocation', () => {
  const count = cases.reduce((n,c)=>n+c.rules.length,0);
  assert.equal(count,43);
  for(const c of cases) for(const r of c.rules) assert.doesNotMatch(r,/empty-response|\$response|\$done/);
});
