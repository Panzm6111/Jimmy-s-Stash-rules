/* SPDX-License-Identifier: GPL-3.0-only
 * Derived from NobyDa/Script QuantumultX/File/Wechat.js (see sources.lock.json).
 * Modified 2026-10-19: strict path/schema/error guards; preserve appid and all
 * non-ad fields. Articles only; no chat, Moments or Channels processing.
 * No logging/storage/network. License: licenses/NobyDa-GPL-3.0.txt.
 */
(() => {
  let result = {};
  try {
    const req = typeof $request === 'object' ? $request : {};
    const resp = typeof $response === 'object' ? $response : {};
    if (!/^https:\/\/mp\.weixin\.qq\.com\/mp\/getappmsgad\/?(?:\?|$)/.test(String(req.url || ''))) return;
    if (!['GET', 'POST'].includes(req.method) || typeof resp.body !== 'string' || resp.body.length > 2 * 1024 * 1024) return;
    if (resp.status && !/^2\d\d$/.test(String(resp.status))) return;
    const obj = JSON.parse(resp.body);
    if (!obj || typeof obj !== 'object' || Array.isArray(obj) || obj.success === false || obj.error || obj.error_code) return;
    if (obj.base_resp && obj.base_resp.ret !== 0) return;
    if (!Array.isArray(obj.advertisement_info) || typeof obj.advertisement_num !== 'number') return;
    if (obj.advertisement_info.length || obj.advertisement_num !== 0) {
      obj.advertisement_info = [];
      obj.advertisement_num = 0;
      result = {body: JSON.stringify(obj)};
    }
  } catch (_) {
    // Unknown/error data stays untouched.
  } finally { $done(result); }
})();
