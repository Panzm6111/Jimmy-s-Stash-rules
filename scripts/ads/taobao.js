/* SPDX-License-Identifier: GPL-3.0-only
 * Adapted from fmz200/wool_scripts Scripts/myBlockAds.js (Taobao splash branch).
 * Source revision/checksum: research/sources.lock.json.
 * Modifications 2026-10-19: only the dedicated splash API and taobao-splash items;
 * preserve MTOP envelope, normal sections, products, coupons and payment paths.
 * No generic cloudvideo/poplayer handling, logging, storage or outbound requests.
 * License text: licenses/fmz200-GPL-3.0.txt.
 */
(() => {
  let result = {};
  try {
    const req = typeof $request === 'object' ? $request : {};
    const resp = typeof $response === 'object' ? $response : {};
    const api = 'mtop.taobao.wireless.home.splash.awesome.get';
    if (!/^https:\/\/guide-acs\.m\.taobao\.com\/gw\/mtop\.taobao\.wireless\.home\.splash\.awesome\.get(?:\/\d+(?:\.\d+)*\/?)?(?:\?|$)/.test(String(req.url || ''))) return;
    if (!['GET', 'POST'].includes(req.method) || typeof resp.body !== 'string' || resp.body.length > 2 * 1024 * 1024) return;
    if (resp.status && !/^2\d\d$/.test(String(resp.status))) return;
    const obj = JSON.parse(resp.body);
    if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return;
    if (typeof obj.api === 'string' && obj.api.toLowerCase() !== api) return;
    if (Object.prototype.hasOwnProperty.call(obj, 'ret') && (!Array.isArray(obj.ret) || !obj.ret.length || !obj.ret.every(x => typeof x === 'string' && /^SUCCESS(?:::|$)/.test(x)))) return;
    const sections = obj.data && obj.data.containers && obj.data.containers.splash_home_base && obj.data.containers.splash_home_base.base && obj.data.containers.splash_home_base.base.sections;
    if (!Array.isArray(sections)) return;
    for (const section of sections) {
      const splash = section && section.bizData && section.bizData['taobao-splash'];
      if (!splash || !Array.isArray(splash.data)) continue;
      for (const item of splash.data) {
        if (!item || typeof item !== 'object' || Array.isArray(item)) continue;
        // Only the fields documented by the reviewed upstream splash handler.
        const changes = {waitTime:'0', times:'0', hotStart:'false', coldStart:'false',
          startTime:'3818332800000', endTime:'3818419199000',
          gmtStart:'2090-12-31 00:00:00', gmtEnd:'2090-12-31 23:59:59',
          gmtStartMs:'3818332800000', gmtEndMs:'3818419199000', imgUrl:'', videoUrl:''};
        for (const [key, value] of Object.entries(changes)) {
          if (Object.prototype.hasOwnProperty.call(item, key) && typeof item[key] === 'string') item[key] = value;
        }
      }
    }
    const after = JSON.stringify(obj);
    if (after !== JSON.stringify(JSON.parse(resp.body))) result = {body: after};
  } catch (_) {
    // Unknown/broken responses stay unchanged. Do not log tokens or MTOP payloads.
  } finally {
    $done(result);
  }
})();
