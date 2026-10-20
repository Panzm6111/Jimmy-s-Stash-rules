/* SPDX-License-Identifier: MIT
 * Optional device-only observation. No request values, headers or bodies.
 * Concurrent script runs can overwrite counters: these are diagnostic hints,
 * not exact traffic statistics. Observation never changes an ad result.
 */
function observeAdState(id, version, state) {
  try {
    const modules = ['alipan', 'bilibili', 'cainiao', 'jingdong', 'luckin',
      'meituan', 'taobao', 'tieba', 'wechat-articles', 'weibo', 'xiaohongshu'];
    const states = ['url-unmatched', 'unsupported-method', 'body-unavailable',
      'body-too-large', 'http-error', 'unsupported-status', 'non-json',
      'parse-error', 'unsupported-schema', 'unchanged', 'changed', 'exception'];
    if (!modules.includes(id) || !states.includes(state) ||
        typeof version !== 'string' || !/^AD-\d{8}\.\d+$/.test(version)) return;
    if (typeof $persistentStore === 'undefined' || !$persistentStore) return;
    const store = $persistentStore;
    if (typeof store.read !== 'function' || typeof store.write !== 'function') return;
    const sessionText = store.read('jimmy.ads.diag.session.v1');
    if (typeof sessionText !== 'string' || sessionText.length > 2048) return;
    const session = JSON.parse(sessionText);
    const now = Date.now(), limit = 15 * 60 * 1000;
    if (!session || typeof session !== 'object' || Array.isArray(session) ||
        !Number.isSafeInteger(now) ||
        !Number.isSafeInteger(session.id) || session.id <= 0 || session.id > now ||
        !Number.isSafeInteger(session.until) || now >= session.until ||
        session.until > now + limit || session.until - session.id > limit) return;
    const key = 'jimmy.ads.diag.' + id + '.v1';
    const counts = {};
    const previousText = store.read(key);
    if (typeof previousText === 'string' && previousText.length <= 8192) {
      // Corrupted old counters should not stop the current session recording.
      let previous;
      try { previous = JSON.parse(previousText); } catch (_) {}
      if (previous && !Array.isArray(previous) &&
          previous.sessionId === session.id && previous.version === version &&
          previous.counts && typeof previous.counts === 'object' &&
          !Array.isArray(previous.counts)) {
        for (const known of states) {
          if (!Object.prototype.hasOwnProperty.call(previous.counts, known)) continue;
          const count = previous.counts[known];
          if (Number.isSafeInteger(count) && count >= 0 && count <= 9999) counts[known] = count;
        }
      }
    }
    counts[state] = Math.min(9999, (counts[state] || 0) + 1);
    store.write(JSON.stringify({sessionId: session.id, version, last: now, counts}), key);
  } catch (_) {
    // Missing/failed storage must not affect the response or $done.
  }
}
