/* SPDX-License-Identifier: GPL-3.0-only
 * Adapted from fmz200/wool_scripts Scripts/xiaohongshu/xiaohongshu.js.
 * Original author: fmz200. Source revision and checksum: research/sources.lock.json.
 * Modifications 2026-10-19: splash only; no feed, download, watermark or account
 * changes; no logging, storage or outbound requests; fail open.
 * License text: licenses/fmz200-GPL-3.0.txt.
 */
(() => {
  let result = {};
  try {
    const req = typeof $request === 'object' ? $request : {};
    const resp = typeof $response === 'object' ? $response : {};
    if (!/^https:\/\/edith\.xiaohongshu\.com\/api\/sns\/v\d+\/system_service\/splash_config(?:\?|$)/.test(String(req.url || ''))) return;
    if (!['GET', 'POST'].includes(req.method) || typeof resp.body !== 'string' || resp.body.length > 2 * 1024 * 1024) return;
    if (resp.status && !/^2\d\d$/.test(String(resp.status))) return;
    const obj = JSON.parse(resp.body);
    if (!obj || typeof obj !== 'object' || Array.isArray(obj) || obj.success === false) return;
    if (Object.prototype.hasOwnProperty.call(obj, 'code') && obj.code !== 0) return;
    const groups = obj.data && obj.data.ads_groups;
    if (!Array.isArray(groups) || !groups.length) return;
    // Keep all non-ad fields. Change only the upstream-recognized ad time windows.
    function postpone(item) {
      if (!item || typeof item !== 'object' || Array.isArray(item)) return;
      for (const [key, value] of [['start_time', 3818332800], ['end_time', 3818419199]]) {
        const before = item[key];
        if (typeof before === 'number' && Number.isFinite(before)) item[key] = value;
        else if (typeof before === 'string' && /^\d+$/.test(before)) item[key] = String(value);
      }
    }
    for (const group of groups) {
      postpone(group);
      if (group && Array.isArray(group.ads)) group.ads.forEach(postpone);
    }
    const after = JSON.stringify(obj);
    if (after !== JSON.stringify(JSON.parse(resp.body))) result = {body: after};
  } catch (_) {
    // Unknown/broken responses stay unchanged. Never log response/account data.
  } finally {
    $done(result);
  }
})();
