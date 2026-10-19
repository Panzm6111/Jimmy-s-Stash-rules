/* SPDX-License-Identifier: GPL-3.0-only
 * Endpoint references: fmz200/wool_scripts QuantumultX/rewrite/weibo.snippet.
 * Configuration attribution there: fmz200 / zmqcherish / Keywos.
 * This is a local Stash handler, not a copied remote Weibo cleanup script.
 * Modifications 2026-10-19: only two dedicated splash ad paths; no timeline,
 * messaging, login, notifications, check-in, paid features or storage.
 * Return empty JSON before a network request, matching upstream reject-dict.
 * Keep response mode for existing configs whose remote script updates first.
 * Diagnostics contain fixed codes only; no URL/header/body/exception data.
 * License text: licenses/fmz200-GPL-3.0.txt; source pin: research/sources.lock.json.
 */
(() => {
  let result = {};
  let matched = false;
  let diagnostic = 'unsupported-method';
  try {
    const req = typeof $request === 'object' ? $request : {};
    const url = String(req.url || '');
    const realtime = /^https:\/\/bootrealtime\.uve\.weibo\.com\/v\d+\/ad\/realtime(?:\?|$)/;
    const preload = /^https:\/\/bootpreload\.uve\.weibo\.com\/v\d+\/ad\/preload(?:\?|$)/;
    if (!realtime.test(url) && !preload.test(url)) return;
    matched = true;
    if (!['GET', 'POST'].includes(req.method)) return;
    if (typeof $response === 'object' && $response !== null) {
      // Legacy response handlers must receive a response modification, not the
      // synthetic-response envelope used by request scripts.
      if ($response.status && !/^2\d\d$/.test(String($response.status))) { diagnostic = 'http-error'; return; }
      if ($response.body === '{}') { diagnostic = 'unchanged'; return; }
      result = {body: '{}'};
    } else {
      result = {response: {status: 200, headers: {'Content-Type': 'application/json'}, body: '{}'}};
    }
    diagnostic = 'changed';
  } catch (_) {
    // Never log a request, body or exception.
  } finally {
    if (matched) {
      try { console.log('[JimmyAds][weibo] ' + diagnostic); } catch (_) {}
    }
    $done(result);
  }
})();
