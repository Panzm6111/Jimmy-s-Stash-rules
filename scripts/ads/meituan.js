/* SPDX-License-Identifier: GPL-2.0
 * Derived from blackmatrix7/ios_rule_script script/startup/startup.js (Meituan branch).
 * Modified 2026-10-19: only known ad/mk arrays, preserving other loadInfo fields.
 * No logs/storage/network. License: licenses/blackmatrix7-GPL-2.0.txt; source: sources.lock.json.
 */
(() => {
  let result = {};
  try {
    const req = typeof $request === 'object' ? $request : {};
    const resp = typeof $response === 'object' ? $response : {};
    if (!/^https:\/\/wmapi\.meituan\.com\/api\/v\d+\/loadInfo\/?(?:\?|$)/.test(String(req.url || ''))) return;
    if (!['GET', 'POST'].includes(req.method) || typeof resp.body !== 'string' || resp.body.length > 2 * 1024 * 1024) return;
    if (resp.status && !/^2\d\d$/.test(String(resp.status))) return;
    const obj = JSON.parse(resp.body);
    if (!obj || typeof obj !== 'object' || Array.isArray(obj) || obj.success === false || obj.error || obj.error_code) return;
    if (Object.prototype.hasOwnProperty.call(obj, 'code') && ![0, '0'].includes(obj.code)) return;
    const splash = obj.data && obj.data.startpicture;
    if (!splash || typeof splash !== 'object' || Array.isArray(splash)) return;
    let changed = false;
    for (const key of ['ad', 'mk']) {
      if (Array.isArray(splash[key]) && splash[key].length) { splash[key] = []; changed = true; }
    }
    if (changed) result = {body: JSON.stringify(obj)};
  } catch (_) {
    // Do not discard unknown startup/business data.
  } finally { $done(result); }
})();
