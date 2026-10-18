/* SPDX-License-Identifier: MIT
 * Derived from app2smile/rules js/bilibili-json.js, revision in research/sources.lock.json.
 * Copyright (c) 2023 app2smile. See licenses/app2smile-MIT.txt.
 * Modified 2026-10-18: narrow endpoints, preserve non-ad features, fail open,
 * no URL/body/header logging, no account storage or outbound requests.
 */
(() => {
  let result = {};
  try {
    const req = typeof $request === 'object' ? $request : {};
    const resp = typeof $response === 'object' ? $response : {};
    const path = String(req.url || '').match(/^https:\/\/app\.bilibili\.com(\/x\/v2\/(?:splash\/(?:list|show)|feed\/index))(?:\?|$)/);
    if (!path || req.method !== 'GET' || typeof resp.body !== 'string' || resp.body.length > 2 * 1024 * 1024) return;
    if (resp.status && !/^2\d\d/.test(String(resp.status))) return;
    const body = JSON.parse(resp.body);
    if (!body || body.code !== 0 || !body.data || typeof body.data !== 'object' || Array.isArray(body.data)) return;
    let changed = false;
    if (path[1].startsWith('/x/v2/splash/')) {
      if (Object.prototype.hasOwnProperty.call(body.data, 'show')) {
        delete body.data.show;
        changed = true;
      }
    } else if (Array.isArray(body.data.items)) {
      const before = body.data.items;
      const adTypes = ['ad_web_s', 'ad_av', 'ad_web_gif', 'ad_player', 'ad_inline_3d', 'ad_inline_eggs'];
      const after = before.filter(item => {
        if (!item || typeof item !== 'object') return true;
        if (item.card_type === 'cm_v2' && adTypes.includes(item.card_goto)) return false;
        if (item.card_type === 'cm_double_v9' && item.card_goto === 'ad_inline_av') return false;
        if (item.card_type === 'banner_v8' && item.card_goto === 'banner' && Array.isArray(item.banner_item)) {
          // 不丢弃整个 banner：只删明确标为 ad 的条目。
          item.banner_item = item.banner_item.filter(v => !v || v.type !== 'ad');
        }
        return true;
      });
      body.data.items = after;
      changed = JSON.stringify(body.data.items) !== JSON.stringify(JSON.parse(resp.body).data.items);
    }
    if (changed) result = {body: JSON.stringify(body)};
  } catch (_) {
    // Stash 的空修改对象保留原响应。不输出异常内容，避免泄露响应数据。
  } finally {
    $done(result);
  }
})();
