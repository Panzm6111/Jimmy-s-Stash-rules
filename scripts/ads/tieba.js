/* SPDX-License-Identifier: MIT
 * Derived from app2smile/rules js/tieba-json.js, revision in research/sources.lock.json.
 * Copyright (c) 2023 app2smile. See licenses/app2smile-MIT.txt.
 * Modified 2026-10-18: only splash JSON; fail open; no logging or outbound requests.
 */
(() => {
  let result = {};
  try {
    const req = typeof $request === 'object' ? $request : {};
    const resp = typeof $response === 'object' ? $response : {};
    if (!/^https:\/\/tiebac\.baidu\.com\/c\/f\/ad\/getSplashAd(?:\?|$)/.test(String(req.url || ''))) return;
    if (typeof resp.body !== 'string' || resp.body.length > 1024 * 1024) return;
    if (resp.status && !/^2\d\d/.test(String(resp.status))) return;
    const body = JSON.parse(resp.body);
    if (body && body.error_code === 0 && Object.prototype.hasOwnProperty.call(body, 'data')) {
      body.error_code = 2230209;
      body.data = null;
      result = {body: JSON.stringify(body)};
    }
  } catch (_) {
    // 返回原始内容；不记录请求或响应。
  } finally {
    $done(result);
  }
})();
