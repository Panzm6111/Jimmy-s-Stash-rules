/* SPDX-License-Identifier: GPL-3.0-only
 * Derived from fmz200/wool_scripts Scripts/adrive/adrive.js; see sources.lock.json.
 * Modified 2026-10-19: only four banner anchors; keep backups, news, sign-in and
 * account features. No logs, storage or network. License: licenses/fmz200-GPL-3.0.txt.
 */
(() => {
  let result = {};
  try {
    const req = typeof $request === 'object' ? $request : {};
    const resp = typeof $response === 'object' ? $response : {};
    if (!/^https:\/\/member\.alipan\.com\/v1\/users\/onboard_list\/?(?:\?|$)/.test(String(req.url || ''))) return;
    if (!['GET', 'POST'].includes(req.method) || typeof resp.body !== 'string' || resp.body.length > 2 * 1024 * 1024) return;
    if (resp.status && !/^2\d\d$/.test(String(resp.status))) return;
    const obj = JSON.parse(resp.body);
    if (!obj || typeof obj !== 'object' || Array.isArray(obj) || obj.success === false || obj.error || obj.error_code) return;
    if (Object.prototype.hasOwnProperty.call(obj, 'code') && ![0, '0', 200, '200', 'Success'].includes(obj.code)) return;
    if (!Array.isArray(obj.result)) return;
    const ads = ['backup_top_banner', 'home_top_banner', 'resource_top_banner', 'video_top_banner'];
    const filtered = obj.result.filter(item => !item || !ads.includes(item.anchor));
    if (filtered.length !== obj.result.length) {
      obj.result = filtered;
      result = {body: JSON.stringify(obj)};
    }
  } catch (_) {
    // Keep the original response on unknown/error data.
  } finally { $done(result); }
})();
