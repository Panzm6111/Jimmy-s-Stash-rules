/* SPDX-License-Identifier: GPL-3.0-only
 * Endpoint references: fmz200/wool_scripts QuantumultX/rewrite/weibo.snippet.
 * Configuration attribution there: fmz200 / zmqcherish / Keywos.
 * This is a local Stash response handler, not a copied remote Weibo cleanup script.
 * Modifications 2026-10-19: only two dedicated splash ad paths; no timeline,
 * messaging, login, notifications, check-in, paid features, logging or storage.
 * License text: licenses/fmz200-GPL-3.0.txt; source pin: research/sources.lock.json.
 */
(() => {
  let result = {};
  try {
    const req = typeof $request === 'object' ? $request : {};
    const resp = typeof $response === 'object' ? $response : {};
    const url = String(req.url || '');
    const realtime = /^https:\/\/bootrealtime\.uve\.weibo\.com\/v\d+\/ad\/realtime(?:\?|$)/;
    const preload = /^https:\/\/bootpreload\.uve\.weibo\.com\/v\d+\/ad\/preload(?:\?|$)/;
    if (!realtime.test(url) && !preload.test(url)) return;
    if (!['GET', 'POST'].includes(req.method) || typeof resp.body !== 'string' || resp.body.length > 1024 * 1024) return;
    if (resp.status && !/^2\d\d$/.test(String(resp.status))) return;
    const obj = JSON.parse(resp.body);
    if (!obj || typeof obj !== 'object' || Array.isArray(obj) || !Object.keys(obj).length) return;
    if (obj.success === false || obj.error || obj.error_code) return;
    if (Object.prototype.hasOwnProperty.call(obj, 'code') && (!/^\d+$/.test(String(obj.code)) || Number(obj.code) >= 400)) return;
    // Upstream uses reject-dict only at these ad endpoints. Empty dictionary is
    // emitted via the same Stash response API as the other local ad handlers.
    result = {body: '{}'};
  } catch (_) {
    // Non-JSON/unknown failures retain the original response without logging it.
  } finally {
    $done(result);
  }
})();
