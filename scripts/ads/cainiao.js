/* SPDX-License-Identifier: GPL-3.0-only
 * Derived from fmz200/wool_scripts Scripts/cainiao/cainiao.js; see sources.lock.json.
 * Modified 2026-10-19: only explicit adItemDetail entries in ads.show. Preserve
 * coupons, points, package import, messages and ordinary cards. No logs/storage/network.
 * License: licenses/fmz200-GPL-3.0.txt.
 */
(() => {
  let result = {};
  try {
    const req = typeof $request === 'object' ? $request : {};
    const resp = typeof $response === 'object' ? $response : {};
    if (!/^https:\/\/cn-acs\.m\.cainiao\.com\/gw\/mtop\.cainiao\.guoguo\.nbnetflow\.ads\.show\.cn(?:\/[0-9]+(?:\.[0-9]+)*)?\/?(?:\?|$)/.test(String(req.url || ''))) return;
    if (!['GET', 'POST'].includes(req.method) || typeof resp.body !== 'string' || resp.body.length > 2 * 1024 * 1024) return;
    if (resp.status && !/^2\d\d$/.test(String(resp.status))) return;
    const obj = JSON.parse(resp.body);
    if (!obj || typeof obj !== 'object' || Array.isArray(obj) || obj.success === false || obj.error || obj.error_code) return;
    if (Object.prototype.hasOwnProperty.call(obj, 'code') && ![0, '0'].includes(obj.code)) return;
    if (Object.prototype.hasOwnProperty.call(obj, 'ret') && (!Array.isArray(obj.ret) || !obj.ret.length || !obj.ret.every(value => typeof value === 'string' && /^SUCCESS(?:::|$)/.test(value)))) return;
    const items = obj.data && obj.data.result;
    if (!Array.isArray(items)) return;
    const filtered = items.filter(item => !(item && item.materialContentMapper && item.materialContentMapper.adItemDetail));
    if (items.length !== filtered.length) {
      obj.data.result = filtered;
      result = {body: JSON.stringify(obj)};
    }
  } catch (_) {
    // Do not log response bodies or request headers.
  } finally { $done(result); }
})();
