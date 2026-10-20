'use strict';
// Mock storage/time and reconstructed JSON only; no native Stash/iPhone claim.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const observer = fs.readFileSync(path.join(root, 'tools/ad_observation_runtime.js'), 'utf8');
const generator = fs.readFileSync(path.join(root, 'tools/build_ad_scripts.py'), 'utf8');
const runtime = generator.match(/RUNTIME = r'''([\s\S]*?)'''/)[1];
const version = generator.match(/VERSION = '([^']+)'/)[1];
const moduleId = 'xiaohongshu';
const sessionKey = 'jimmy.ads.diag.session.v1';
const moduleKey = 'jimmy.ads.diag.' + moduleId + '.v1';
const now = 1792486800000;
const limit = 15 * 60 * 1000;
const session = {id: now, until: now + limit};
const url = 'https://edith.xiaohongshu.com/api/sns/v1/system_service/splash_config';
const source = fs.readFileSync(path.join(root, 'tools/ad_transforms/xiaohongshu.js'), 'utf8');
// Exercise the actual generator runtime before/after regeneration, rather than
// depending on whichever generated JS happened to exist when this test started.
const script = runtime
  .replace('__VERSION__', JSON.stringify(version))
  .replace('__ID__', JSON.stringify(moduleId))
  .replace('__OBSERVATION__', observer)
  .replace('__PATTERNS__', JSON.stringify(['^https://edith\\.xiaohongshu\\.com/api/sns/v1/system_service/splash_config(?:\\?|$)']))
  .replace('__METHODS__', JSON.stringify(['GET', 'POST']))
  .replace('__TRANSFORM__', source.slice(source.indexOf('*/') + 2));

function storage(initial = {}) {
  const data = new Map(Object.entries(initial)), writes = [], reads = [];
  return {
    data, writes, reads,
    read(key) { reads.push(key); return data.get(key) ?? null; },
    write(value, key) { writes.push({key, value}); data.set(key, value); return true; }
  };
}
function observe(store, {clock = now, id = moduleId, revision = version, state = 'changed'} = {}) {
  const ctx = {Date: {now: () => clock}, $persistentStore: store};
  vm.runInNewContext(observer + '\nobserveAdState(' +
    [id, revision, state].map(x => JSON.stringify(x)).join(',') + ');', ctx, {timeout: 1000});
}
function execute(store, argument = 'diagnostic=0') {
  const done = [], logs = [];
  vm.runInNewContext(script, {
    Date: {now: () => now}, $persistentStore: store, $argument: argument,
    $request: {url: url + '?token=EXAMPLE_NOT_A_SECRET', method: 'GET',
      headers: {Cookie: 'PRIVATE_SENTINEL', Authorization: 'PRIVATE_SENTINEL'},
      body: 'PRIVATE_SENTINEL'},
    $response: {status: 200, headers: {'Set-Cookie': 'PRIVATE_SENTINEL'},
      body: JSON.stringify({code: 0, data: {ads_groups: [{id: 'simulated-ad'}]},
        account: 'PRIVATE_SENTINEL'})},
    console: {log: value => logs.push(value)}, $done: value => done.push(value)
  }, {timeout: 1000});
  assert.equal(done.length, 1);
  assert.equal(JSON.parse(done[0].body).data.ads_groups[0].start_time, 3818332800);
  assert.equal(JSON.parse(done[0].body).account, 'PRIVATE_SENTINEL');
  return logs;
}

test('observation is silent and never writes without an explicitly valid session', () => {
  for (const raw of [undefined, '', 'broken', 'null', '[]', '{}',
    JSON.stringify({id: String(now), until: now + limit}),
    JSON.stringify({id: now, until: String(now + limit)}),
    JSON.stringify({id: now + 1, until: now + limit}),
    JSON.stringify({id: now - limit, until: now}),
    JSON.stringify({id: now, until: now + limit + 1}),
    JSON.stringify({id: now - limit, until: now + 1}),
    JSON.stringify({id: -1, until: now + 1})]) {
    const store = storage(raw === undefined ? {} : {[sessionKey]: raw});
    assert.deepEqual(execute(store), []);
    assert.deepEqual(store.writes, []);
    assert.deepEqual(store.reads, [sessionKey]);
  }
});

test('observation records from session start through the final millisecond and stops at expiry', () => {
  const store = storage({[sessionKey]: JSON.stringify(session)});
  for (const clock of [now, now + limit - 1]) observe(store, {clock});
  assert.equal(store.writes.length, 2);
  const record = JSON.parse(store.data.get(moduleKey));
  assert.deepEqual(record, {sessionId: now, version, last: now + limit - 1, counts: {changed: 2}});
  observe(store, {clock: now + limit});
  observe(store, {clock: now + limit + 1});
  assert.equal(store.writes.length, 2);
});

test('only current session and script version counters are retained', () => {
  for (const previous of [
    {sessionId: now - 1, version, last: now, counts: {changed: 8}},
    {sessionId: now, version: 'AD-20261020.1', last: now, counts: {changed: 8}},
    {sessionId: String(now), version, last: now, counts: {changed: 8}}
  ]) {
    const store = storage({[sessionKey]: JSON.stringify(session), [moduleKey]: JSON.stringify(previous)});
    observe(store);
    assert.deepEqual(JSON.parse(store.data.get(moduleKey)), {sessionId: now, version, last: now, counts: {changed: 1}});
  }
});

test('contaminated old JSON is filtered to bounded fixed-state integer counts', () => {
  const previous = JSON.stringify({sessionId: now, version, last: 'PRIVATE_SENTINEL',
    url: 'PRIVATE_SENTINEL', counts: {
      changed: 9999, unchanged: 2, exception: -1, 'http-error': 1.5,
      'non-json': '5', 'parse-error': 10000, 'body-unavailable': null,
      PRIVATE_SENTINEL: 3, '__proto__': {PRIVATE_SENTINEL: 1}
    }});
  const store = storage({[sessionKey]: JSON.stringify(session), [moduleKey]: previous});
  observe(store);
  assert.deepEqual(JSON.parse(store.data.get(moduleKey)), {
    sessionId: now, version, last: now, counts: {unchanged: 2, changed: 9999}
  });
  assert.doesNotMatch(store.writes[0].value, /PRIVATE_SENTINEL|__proto__/);
  for (const value of ['broken', 'null', '[]', '"PRIVATE_SENTINEL"', 'x'.repeat(8193)]) {
    store.data.set(moduleKey, value);
    observe(store);
    assert.deepEqual(JSON.parse(store.data.get(moduleKey)).counts, {changed: 1});
  }
});

test('unknown status/module/version cannot create arbitrary storage keys or values', () => {
  for (const options of [
    {state: 'PRIVATE_SENTINEL'}, {id: 'PRIVATE_SENTINEL'},
    {revision: 'PRIVATE_SENTINEL'}, {state: '__proto__'}, {state: 'constructor'}
  ]) {
    const store = storage({[sessionKey]: JSON.stringify(session)});
    observe(store, options);
    assert.deepEqual(store.writes, []);
    assert.deepEqual(store.reads, []);
  }
});

test('active recording preserves ad result and stores no request or response values', () => {
  const store = storage({[sessionKey]: JSON.stringify(session)});
  assert.deepEqual(execute(store), []);
  assert.equal(store.writes.length, 1);
  assert.deepEqual(JSON.parse(store.writes[0].value), {
    sessionId: now, version, last: now, counts: {changed: 1}
  });
  assert.deepEqual(store.reads, [sessionKey, moduleKey]);
  assert.doesNotMatch(JSON.stringify(store.writes), /PRIVATE_SENTINEL|https:|Cookie|Authorization|simulated-ad|token/);
});

test('missing storage, read/write failures and failed writes never change done or transformation', () => {
  for (const store of [
    undefined, null, {},
    new Proxy({}, {get() {throw Error('PRIVATE_SENTINEL');}}),
    {read() {throw Error('PRIVATE_SENTINEL');}, write() {}},
    {read: key => key === sessionKey ? JSON.stringify(session) : null,
      write() {throw Error('PRIVATE_SENTINEL');}},
    {read: key => key === sessionKey ? JSON.stringify(session) : null, write: () => false}
  ]) assert.deepEqual(execute(store), []);
  const store = {read(key) {if (key === sessionKey) return JSON.stringify(session); throw Error('PRIVATE_SENTINEL');}, write() {}};
  assert.deepEqual(execute(store), []);
});

test('legacy diagnostic argument still emits exactly its fixed log without requiring a session', () => {
  for (const store of [undefined, storage(), storage({[sessionKey]: JSON.stringify(session)})]) {
    assert.deepEqual(execute(store, 'diagnostic=1'), [`[JimmyAds][${moduleId}][${version}] changed`]);
  }
});
