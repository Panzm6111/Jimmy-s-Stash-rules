/* SPDX-License-Identifier: GPL-3.0-only
 * Endpoint and successful empty-ad result from fmz200/wool_scripts rewrite.snippet.
 * Modified 2026-10-19: only a successful dedicated adposNew JSON response; no
 * product, coupon, exchange or order endpoints. No logging/storage/network.
 * License: licenses/fmz200-GPL-3.0.txt. Source: sources.lock.json.
 */
(() => {
  let result = {};
  try {
    const req = typeof $request === 'object' ? $request : {};
    const resp = typeof $response === 'object' ? $response : {};
    if (!/^https:\/\/capi\.lkcoffee\.com\/resource\/m\/sys\/app\/adposNew\/?(?:\?|$)/.test(String(req.url || ''))) return;
    if (!['GET', 'POST'].includes(req.method) || typeof resp.body !== 'string' || resp.body.length > 1024 * 1024) return;
    if (resp.status && !/^2\d\d$/.test(String(resp.status))) return;
    const obj = JSON.parse(resp.body);
    if (!obj || typeof obj !== 'object' || Array.isArray(obj) || obj.status !== 'SUCCESS' || obj.error || obj.error_code || obj.success === false) return;
    if (Object.prototype.hasOwnProperty.call(obj, 'code') && ![0, '0', 200, '200'].includes(obj.code)) return;
    if (Object.keys(obj).some(key => key !== 'status')) result = {body: JSON.stringify({status: 'SUCCESS'})};
  } catch (_) {
    // Original failures remain visible; no fabricated account success.
  } finally { $done(result); }
})();
