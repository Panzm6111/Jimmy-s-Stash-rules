const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const catalog = JSON.parse(fs.readFileSync(path.join(root, 'research/ad-catalog.json')));
const source = fs.readFileSync(path.join(root, 'scripts/ads/empty-response.js'), 'utf8');
const cases = catalog.modules.flatMap(m => m.rewrite
  .filter(r => ['reject-dict', 'reject-200'].includes(r.upstream_action))
  .map(r => ({...r, id: m.id})));

function run(url, method = 'GET', extra = {}) {
  const results = [], logs = [];
  const context = {
    $request: {url, method, headers: {Cookie: 'PRIVATE_TEST_VALUE'}, body: 'PRIVATE_TEST_VALUE'},
    $done: result => results.push(result),
    console: {log: (...args) => logs.push(args.join(' '))},
    ...extra
  };
  vm.runInNewContext(source, context, {timeout: 1000});
  assert.equal(results.length, 1, 'must finish exactly once');
  assert.ok(!logs.join().includes('PRIVATE_TEST_VALUE'));
  return {result: JSON.parse(JSON.stringify(results[0])), logs};
}

test('dedicated endpoints return source-intended JSON or empty 200 without reading upstream', () => {
  assert.equal(cases.length, 16);
  for (const item of cases) {
    for (const method of ['GET', 'POST']) {
      const {result, logs} = run(item.positive + '&secret=PRIVATE_TEST_VALUE', method);
      assert.equal(result.response.status, 200);
      assert.equal(result.response.body, item.upstream_action === 'reject-dict' ? '{}' : '');
      assert.equal(result.response.headers['Cache-Control'], 'no-store');
      assert.equal(logs.length, 1);
      assert.match(logs[0], /^\[JimmyAds\]\[[a-z0-9-]+\] empty-(json|200)$/);
      assert.deepEqual(run(item.positive, method).result, result, 'repeat produces no extra side effects');
    }
  }
});

test('business paths, foreign hosts, unsupported methods and response phase pass through', () => {
  for (const item of cases) {
    for (const url of [...item.negative, item.positive.replace('://', '://unrelated.')]) {
      assert.deepEqual(run(url), {result: {}, logs: []});
    }
    for (const method of ['PUT', 'DELETE', 'OPTIONS', 'HEAD']) {
      assert.deepEqual(run(item.positive, method), {result: {}, logs: []});
    }
    assert.deepEqual(run(item.positive, 'GET', {$response: {status: 200, body: 'PRIVATE_TEST_VALUE'}}), {result: {}, logs: []});
  }
});

test('missing request and a broken log sink still finish safely', () => {
  assert.deepEqual(run('', 'GET', {$request: undefined}).result, {});
  const {result} = run(cases[0].positive, 'GET', {console: {log() { throw new Error('PRIVATE_TEST_VALUE'); }}});
  assert.equal(result.response.status, 200);
});
