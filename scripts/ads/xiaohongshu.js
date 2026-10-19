/* SPDX-License-Identifier: GPL-3.0-only
 * Adapted from fmz200/wool_scripts Scripts/xiaohongshu/xiaohongshu.js.
 * Original author: fmz200. Source revision and checksum: research/sources.lock.json.
 * Modifications 2026-10-19: splash only; no feed, download, watermark or account
 * changes; no storage or outbound requests; fail open.
 * Diagnostics use fixed codes only, never URL/header/body/exception data.
 * Restore upstream's missing start/end fields for recognized ad records.
 * License text: licenses/fmz200-GPL-3.0.txt.
 */
(() => {
  let result = {};
  let matched = false;
  let diagnostic = 'unsupported-body';
  try {
    const req = typeof $request === 'object' ? $request : {};
    const resp = typeof $response === 'object' ? $response : {};
    if (!/^https:\/\/edith\.xiaohongshu\.com\/api\/sns\/v\d+\/system_service\/splash_config(?:\?|$)/.test(String(req.url || ''))) return;
    matched = true;
    if (!['GET', 'POST'].includes(req.method) || typeof resp.body !== 'string' || resp.body.length > 2 * 1024 * 1024) return;
    if (resp.status && !/^2\d\d$/.test(String(resp.status))) { diagnostic = 'http-error'; return; }
    const obj = JSON.parse(resp.body);
    diagnostic = 'unsupported-schema';
    if (!obj || typeof obj !== 'object' || Array.isArray(obj) || obj.success === false) return;
    if (Object.prototype.hasOwnProperty.call(obj, 'code') && obj.code !== 0) return;
    const groups = obj.data && obj.data.ads_groups;
    if (!Array.isArray(groups)) return;
    let supported = groups.length === 0;
    // Keep all non-ad fields. Change only the upstream-recognized ad time windows.
    function postpone(item) {
      if (!item || typeof item !== 'object' || Array.isArray(item) || !Object.keys(item).length) return;
      // A structured/non-numeric time field signals an unknown schema. Keep
      // that record unchanged instead of inventing a conversion.
      for (const key of ['start_time', 'end_time']) {
        if (!Object.prototype.hasOwnProperty.call(item, key)) continue;
        if (!(typeof item[key] === 'number' && Number.isFinite(item[key])) &&
            !(typeof item[key] === 'string' && /^\d+$/.test(item[key]))) return;
      }
      supported = true;
      for (const [key, value] of [['start_time', 3818332800], ['end_time', 3818419199]]) {
        const before = item[key];
        if (!Object.prototype.hasOwnProperty.call(item, key) || typeof before === 'number') item[key] = value;
        else if (typeof before === 'string' && /^\d+$/.test(before)) item[key] = String(value);
      }
    }
    for (const group of groups) {
      postpone(group);
      if (group && Array.isArray(group.ads)) group.ads.forEach(postpone);
    }
    const after = JSON.stringify(obj);
    if (after !== JSON.stringify(JSON.parse(resp.body))) {
      result = {body: after};
      diagnostic = 'changed';
    } else if (supported) diagnostic = 'unchanged';
  } catch (_) {
    // Unknown/broken responses stay unchanged. Never log response/account data.
  } finally {
    if (matched) {
      try { console.log('[JimmyAds][xiaohongshu] ' + diagnostic); } catch (_) {}
    }
    $done(result);
  }
})();
