/* SPDX-License-Identifier: MIT
 * Generated manual self-check, not an advertisement transformation.
 * Native request response envelope and persistentStore API reviewed in:
 * NobyDa/Script@0b8d083d444f4476700cb9d5d059c07b42da85eb
 * Stash/IPA-Installer.stoverride + IPA-Installer/IPA-Installer.js L70,76,112-116,142-146.
 * JS SHA256 c7b2887cafcbe563f022488e04a7fafed9160465fc939f5d0cfa048232216499.
 * Only API conventions are used; no installer business code is copied or run.
 * No request headers/body, account data, URL query values or remote requests.
 */
(() => {
  let output = {};
  const version = 'AD-20261020.4', key = 'jimmy.ads.diag.session.v1';
  const modules = [{"id": "alipan", "name": "阿里云盘广告专项"}, {"id": "bilibili", "name": "哔哩哔哩广告处理"}, {"id": "cainiao", "name": "菜鸟广告专项"}, {"id": "jingdong", "name": "京东广告专项"}, {"id": "luckin", "name": "瑞幸咖啡广告专项"}, {"id": "meituan", "name": "美团广告专项"}, {"id": "taobao", "name": "淘宝开屏广告处理"}, {"id": "tieba", "name": "贴吧开屏广告处理"}, {"id": "wechat-articles", "name": "微信广告专项"}, {"id": "weibo", "name": "微博开屏广告处理"}, {"id": "xiaohongshu", "name": "小红书开屏广告处理"}];
  const labels = {
    'url-unmatched':'脚本已进入，但URL未匹配',
    'unsupported-method':'请求方法不支持',
    'body-unavailable':'响应正文不可用',
    'body-too-large':'响应正文超出处理上限',
    'http-error':'HTTP状态非成功',
    'unsupported-status':'HTTP状态格式不支持',
    'non-json':'正文不是JSON',
    'parse-error':'JSON解析失败',
    'unsupported-schema':'响应结构未支持',
    'unchanged':'已识别，无需修改',
    'changed':'实际产生修改',
    'exception':'脚本执行异常'
  };
  const own = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
  const record = x => !!x && typeof x === 'object' && !Array.isArray(x);
  const integer = x => Number.isSafeInteger(x) && x >= 0;
  const escape = x => String(x).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function parsed(raw) {
    if (typeof raw !== 'string' || raw.length > 8192) throw Error('invalid-storage');
    const value = JSON.parse(raw);
    if (!record(value)) throw Error('invalid-storage');
    return value;
  }
  function sessionValid(s, now) {
    return record(s) && integer(s.id) && s.id > 0 && s.id <= now && integer(s.until) &&
      (s.until === 0 || (s.until >= s.id && s.until - s.id <= 900000));
  }
  function stamp(value) {
    return new Date(value + 8 * 3600000).toISOString().slice(0, 19).replace('T', ' ') + ' 北京时间';
  }
  try {
    const req = typeof $request === 'object' && $request ? $request : {};
    if (req.method !== 'GET' || typeof req.url !== 'string') return;
    const match = /^http(s?):\/\/example\.com(?::(?:80|443))?\/jimmy-stash-check\/?(?:\?(start=1|stop=1))?$/.exec(req.url);
    if (!match) return;
    const protocol = match[1] ? 'https' : 'http', action = match[2] || '';
    const now = Date.now();
    let store = null, session = null, unavailable = false, damaged = false, command = '';
    try {
      if (typeof $persistentStore === 'undefined' || !$persistentStore ||
          typeof $persistentStore.read !== 'function' || typeof $persistentStore.write !== 'function') throw Error('no-storage');
      store = $persistentStore;
      const raw = store.read(key);
      if (raw !== null && raw !== undefined && raw !== '') {
        session = parsed(raw);
        if (!sessionValid(session, now)) throw Error('invalid-session');
      }
    } catch (_) {
      unavailable = true;
      session = null;
    }
    if (action && store) {
      try {
        function saveSession(next) {
          if (!sessionValid(next, now) || store.write(JSON.stringify(next), key) !== true) throw Error('write-failed');
          const saved = parsed(store.read(key));
          if (!sessionValid(saved, now) || saved.id !== next.id || saved.until !== next.until) throw Error('readback-failed');
        }
        if (action === 'start=1') {
          const next = {id: now, until: now + 900000};
          saveSession(next);
          session = next;
          unavailable = false;
          command = '已开始15分钟诊断。请先返回结果页，再打开需要检查的App。';
        } else if (session) {
          const next = {id: session.id, until: 0};
          saveSession(next);
          session = next;
          command = '已停止记录；本轮已有结果仍保留在设备。';
        } else {
          command = '没有可停止的有效诊断会话。';
        }
      } catch (_) {
        unavailable = true;
        command = '本机存储写入失败或读回核对失败，无法确认诊断已开始或停止。';
      }
    } else if (action) {
      command = '本机存储不可用，无法开始或停止诊断。';
    }
    const active = !unavailable && session && session.until > now;
    let total = 0;
    const rows = modules.map(module => {
      let value = null, trouble = false;
      if (session && store && !unavailable) {
        try {
          const raw = store.read('jimmy.ads.diag.' + module.id + '.v1');
          if (raw !== null && raw !== undefined && raw !== '') {
            const candidate = parsed(raw);
            if (!integer(candidate.sessionId)) throw Error('invalid-record');
            if (candidate.sessionId === session.id) {
              if (typeof candidate.version !== 'string' || !/^AD-\d{8}\.\d{1,4}$/.test(candidate.version) ||
                  !integer(candidate.last) || candidate.last < session.id || candidate.last > now ||
                  !record(candidate.counts) || Object.keys(candidate.counts).some(k => !own(labels,k) || !integer(candidate.counts[k]) || candidate.counts[k] > 9999)) {
                throw Error('invalid-record');
              }
              value = candidate;
            }
          }
        } catch (_) {
          trouble = damaged = true;
        }
      }
      const counts = value ? Object.keys(labels).filter(k => value.counts[k] > 0)
        .map(k => { total += value.counts[k]; return escape(labels[k]) + '：' + value.counts[k]; }).join('<br>') : '';
      const detail = trouble ? '本机记录损坏或读取失败；无法记录/读取该模块状态。' :
        value ? '脚本 ' + escape(value.version) + '<br>最后记录：' + stamp(value.last) + '<br>' + (counts || '本轮尚无有效命中计数') :
        '本轮没有记录';
      return '<tr><th scope="row">' + escape(module.name) + '</th><td>' + detail + '</td></tr>';
    }).join('');
    const sessionText = unavailable ? '本机诊断存储不可用或数据损坏，当前无法可靠记录。自检页仍可显示。' :
      !session ? '尚未开始诊断，默认不记录。' :
      active ? '记录中，将于 ' + stamp(session.until) + ' 自动停止新增记录。' :
      session.until === 0 ? '已手动停止；不再新增记录。' : '15分钟已结束；不再新增记录。';
    const empty = total === 0 ? '<p>目前没有本轮处理记录。这不能直接证明MITM失败：可能尚未发出新请求、URL未匹配、脚本资源未更新、使用缓存或流量没有进入HTTP引擎。</p>' : '';
    const body = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
      '<meta name="referrer" content="no-referrer"><title>Jimmy Stash 去广告自检</title>' +
      '<style>body{font:16px/1.65 system-ui,sans-serif;max-width:760px;margin:24px auto;padding:0 18px;color:#202124;background:#fff}' +
      'a{display:inline-block;margin:6px 12px 6px 0}table{width:100%;border-collapse:collapse}th,td{border:1px solid #ddd;padding:10px;text-align:left;vertical-align:top}' +
      '.notice{background:#eef4ff;padding:12px;border-radius:8px}small{color:#555}</style></head><body>' +
      '<h1>Jimmy Stash 去广告自检</h1><p>页面版本：' + version + '；实际请求协议：<strong>' + protocol + '</strong>。</p>' +
      '<div class="notice">看到此页面，说明本次自检请求已执行Stash请求脚本。' +
      (protocol === 'https' ? '本次HTTPS请求也通过了example.com的解密处理。' : '本次是HTTP请求，尚不能证明HTTPS解密有效。') +
      '这不证明淘宝等App已命中，也不证明开屏广告已去除。</div>' +
      '<h2>检查步骤</h2><ol><li>点“开始15分钟诊断”。</li><li>返回结果页，然后冷启动淘宝、小红书等需要检查的App，等待出现广告或进入首页。</li>' +
      '<li>回到Safari的结果页，点“刷新结果”；不要重复点开始，否则会开始新一轮。</li></ol>' +
      '<p><a href="/jimmy-stash-check?start=1">开始15分钟诊断</a><a href="/jimmy-stash-check">返回结果页 / 刷新结果</a>' +
      '<a href="/jimmy-stash-check?stop=1">停止记录</a></p>' +
      (command ? '<p class="notice">' + command + '</p>' : '') + '<p>' + sessionText + '</p>' +
      (action ? '<p><strong>请点“返回结果页 / 刷新结果”后再切换App，避免刷新带开始参数的页面重置本轮。</strong></p>' : '') +
      (damaged ? '<p>部分模块记录不可读取；页面没有显示其中的内容，请重新开始一轮诊断。</p>' : '') + empty +
      '<h2>响应脚本状态</h2><table><thead><tr><th>模块</th><th>本轮结果</th></tr></thead><tbody>' + rows + '</tbody></table>' +
      '<p>这里仅统计响应脚本；原生URL拒绝和域名拦截不经过这些脚本，所以不会显示在表内。计数说明执行状态，不能单凭次数判断广告效果。</p>' +
      '<p>仅在设备保存模块、版本、时间及固定状态计数；不保存或上传Cookie、账号、请求地址、请求头或正文。到期或手动停止后，已有结果保留，但不再新增。</p>' +
      '<p>本自检只新增example.com这个精确解密主机；该主机HTTPS连接可进入解密，脚本只处理本自检路径，不改变任何App的数据处理策略。</p>' +
      '<p><small>Safari可能自动将HTTP升级HTTPS，请以上面的“实际请求协议”为准。此页面没有外部资源或上传功能。</small></p></body></html>';
    output = {response: {status: 200, headers: {'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'}, body}};
  } catch (_) {
    // Do not log an exception: host errors can contain private request data.
  } finally {
    $done(output);
  }
})();
