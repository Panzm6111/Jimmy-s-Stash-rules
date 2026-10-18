/* SPDX-License-Identifier: GPL-2.0
 * Derived from blackmatrix7/ios_rule_script script/startup/startup.js (JD branch).
 * Source revision/checksum: sources.lock.json. License: licenses/blackmatrix7-GPL-2.0.txt.
 * Modified 2026-10-19: strict URL/response guards; only existing display counts
 * and durations; preserve product/order/coupon data. No logging, storage or requests.
 */
(() => {
  let result = {};
  try {
    const req = typeof $request === 'object' ? $request : {};
    const resp = typeof $response === 'object' ? $response : {};
    const url = String(req.url || '');
    if (!/^https:\/\/api\.m\.jd\.com\/client\.action\?[^#]*$/.test(url)) return;
    const functions = url.split('?')[1].split('&').filter(part => /^functionId=/.test(part));
    if (functions.length !== 1 || functions[0] !== 'functionId=start') return;
    if (!['GET', 'POST'].includes(req.method) || typeof resp.body !== 'string' || resp.body.length > 2 * 1024 * 1024) return;
    if (resp.status && !/^2\d\d$/.test(String(resp.status))) return;
    const obj = JSON.parse(resp.body);
    if (!obj || typeof obj !== 'object' || Array.isArray(obj) || obj.success === false || obj.error || obj.error_code) return;
    if (Object.prototype.hasOwnProperty.call(obj, 'code') && ![0, '0'].includes(obj.code)) return;
    if (!Array.isArray(obj.images) || !obj.images.every(Array.isArray)) return;
    const before = JSON.stringify(obj);
    function zero(item, key) {
      if (typeof item[key] === 'number' && Number.isFinite(item[key])) item[key] = 0;
      else if (typeof item[key] === 'string' && /^\d+$/.test(item[key])) item[key] = '0';
    }
    for (const group of obj.images) {
      for (const ad of group) {
        if (ad && typeof ad === 'object' && !Array.isArray(ad) && Object.prototype.hasOwnProperty.call(ad, 'showTimes')) {
          zero(ad, 'showTimes');
          zero(ad, 'time');
        }
      }
    }
    zero(obj, 'showTimesDaily');
    const body = JSON.stringify(obj);
    if (body !== before) result = {body};
  } catch (_) {
    // Unknown formats and errors pass through unchanged.
  } finally { $done(result); }
})();
