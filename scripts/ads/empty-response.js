/* SPDX-License-Identifier: GPL-3.0-only
 * Dedicated advertising endpoints adapted from fmz200/wool_scripts.
 * Generated from research/ad-catalog.json; edit that catalog, not this file.
 * Native Stash request response API evidence: docs/SOURCES.md.
 * No request body, account data, storage, external requests or notifications.
 */
(() => {
  let result = {};
  let marker = '';
  try {
    const req = typeof $request === 'object' && $request ? $request : {};
    // A request script must never modify a response-phase invocation.
    if (typeof $response !== 'undefined' || !['GET', 'POST'].includes(req.method)) return;
    const routes = [
  {
    "id": "damai",
    "match": "^https://acs\\.m\\.taobao\\.com/gw/mtop\\.damai\\.wireless\\.home\\.welcome(?:/[0-9]+(?:\\.[0-9]+)*)?/?(?:\\?|$)",
    "json": false
  },
  {
    "id": "amap",
    "match": "^https://m5\\.amap\\.com/ws/shield/dsp/app/startup/init/?(?:\\?|$)",
    "json": true
  },
  {
    "id": "mcdonalds",
    "match": "^https://api\\.mcd\\.cn/bff/portal/home/splash/?(?:\\?|$)",
    "json": false
  },
  {
    "id": "maimai",
    "match": "^https://open\\.taou\\.com/maimai/adshow/?(?:\\?|$)",
    "json": true
  },
  {
    "id": "maimai",
    "match": "^https://h3\\.open\\.taou\\.com/maimai/adshow/?(?:\\?|$)",
    "json": true
  },
  {
    "id": "liepin",
    "match": "^https://api\\-ac\\.liepin\\.com/api/com\\.liepin\\.cyclops\\.live\\.get-ad-cards/?(?:\\?|$)",
    "json": true
  },
  {
    "id": "mijia",
    "match": "^https://home\\.mi\\.com/cgi-op/api/v1/(?:recommendation|resource/realtime)/openingBanner/?(?:\\?|$)",
    "json": true
  },
  {
    "id": "netease-mail",
    "match": "^https://appconf\\.mail\\.163\\.com/mmad/[^?#]*(?:\\?|$)",
    "json": false
  },
  {
    "id": "netease-music",
    "match": "^https://interface\\.music\\.163\\.com/e?api/ad(?:/[^?#]*)?(?:\\?|$)",
    "json": true
  },
  {
    "id": "netease-music",
    "match": "^https://interface3\\.music\\.163\\.com/e?api/ad(?:/[^?#]*)?(?:\\?|$)",
    "json": true
  },
  {
    "id": "netease-music",
    "match": "^https://ipv4\\.music\\.163\\.com/e?api/ad(?:/[^?#]*)?(?:\\?|$)",
    "json": true
  },
  {
    "id": "xianyu",
    "match": "^https://acs\\.m\\.goofish\\.com/gw/mtop\\.taobao\\.idlecommerce\\.splash\\.ads(?:/[0-9]+(?:\\.[0-9]+)*)?/?(?:\\?|$)",
    "json": true
  },
  {
    "id": "xiaoyuzhou",
    "match": "^https://api\\.xiaoyuzhoufm\\.com/v\\d+/flash/?(?:\\?|$)",
    "json": true
  },
  {
    "id": "wps",
    "match": "^https://mobile\\-pic\\.cache\\.iciba\\.com/feeds_ad/[^?#]*(?:\\?|$)",
    "json": false
  },
  {
    "id": "zhihu",
    "match": "^https://api\\.zhihu\\.com/commercial_api/(?:launch_v2|real_time_launch_v2|banners_v3/app_topstory_banner)/?(?:\\?|$)",
    "json": true
  },
  {
    "id": "zhihu",
    "match": "^https://api\\.zhihu\\.com/ad-style-service/request/?(?:\\?|$)",
    "json": true
  }
];
    const hit = routes.find(route => new RegExp(route.match).test(String(req.url || '')));
    if (!hit) return;
    result = {response: {
      status: 200,
      headers: {'Content-Type': hit.json ? 'application/json; charset=utf-8' : 'text/plain; charset=utf-8',
                'Cache-Control': 'no-store'},
      body: hit.json ? '{}' : ''
    }};
    marker = '[JimmyAds][' + hit.id + '] ' + (hit.json ? 'empty-json' : 'empty-200');
  } catch (_) {
    // Unexpected runtime errors pass through; never print the exception.
  } finally {
    if (marker) { try { console.log(marker); } catch (_) {} }
    $done(result);
  }
})();
