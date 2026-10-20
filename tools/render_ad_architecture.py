#!/usr/bin/env python3
"""Keep the detailed ad specification and review hashes aligned with live sources.

Edit prose before the marker in docs/AD-ARCHITECTURE.md; the exact declaration,
module table, hashes and complete JS appendix below it are generated.
"""
import argparse
import hashlib
import json
from pathlib import Path
import yaml
from build_ad_scripts import VERSION
from validate import ROOT, load, merged

DOC = 'docs/AD-ARCHITECTURE.md'
MARKER = '<!-- GENERATED-AD-SPEC -->'
AUDIT = 'research/ad-architecture-audit.json'

def rendered():
    prefix = (ROOT / DOC).read_text().split(MARKER,1)[0].rstrip() + '\n\n' + MARKER + '\n'
    modules = sorted(p.relative_to(ROOT) for p in (ROOT / 'modules/ads').glob('*.stoverride') if p.stem != 'expanded')
    parsed = [(p,load(p)) for p in modules]
    config = merged(*modules)
    config['http']['mitm'] = sorted(set(config['http']['mitm']))
    main = load('config/stash.yaml')
    counts = {'app_modules':len(modules), 'public_main_rules':len(main['rules']),
              'basic_ad_payload':len(load('rules/ads-basic.yaml')['payload']),
              'expanded_ad_payload':len(load('rules/vendor/ads-expanded.yaml')['payload']),
              'app_domain_rules':sum(len(m.get('rules',[])) for _,m in parsed),
              'native_url_rewrites':len(config['http']['url-rewrite']),
              'response_handlers':len(config['http']['script']), 'request_handlers':0,
              'runtime_js_providers':len(config['script-providers']),
              'mitm_exact_hosts':len(config['http']['mitm']), 'optional_probe_js':1}
    out = ['','## 9. 自动核对的当前完整清单','',
           '以下内容直接由现有配置和运行脚本生成。数量描述文件结构，不表示广告效果。','',
           '| 项目 | 实际值 |','|---|---|']
    for k,v in counts.items(): out.append(f'| {k} | {v:,} |')
    out += ['','公共主配置没有HTTP块、没有JS provider；下方HTTP是**全部40款独立模块同时启用时的审阅合并结果**，不是额外需要导入的一份配置。探针另列、默认关闭。','',
            '| App模块 | 路径/真实开关 | 域名路由 | 原生URL动作 | 响应handler | 当前范围 |',
            '|---|---|---|---|---|---|']
    for p,m in parsed:
        h=m.get('http',{})
        out.append(f'| {m["name"]} | [{p.stem}](../{p}) | {len(m.get("rules",[]))} | {len(h.get("url-rewrite",[]))} | {len(h.get("script",[]))} | {m["desc"].replace("|","／")} |')
    declaration={'proxy-groups':[g for g in main['proxy-groups'] if g['name']=='广告拦截'],
                 'rule-providers':main['rule-providers'],
                 'rules':[r for _,m in parsed for r in m.get('rules',[])]+['RULE-SET,基础广告,广告拦截'],
                 'http':config['http'],'script-providers':config['script-providers']}
    out += ['','## 10. 精确原生声明与基础规则原文','',
            '下列原生字段为全量专项的审阅合并片段，缺少完整主配置，不能直接作为主配置导入。主入口实际的LAN/系统例外位于广告RULE-SET之前，后面仍有完整分流与终止MATCH。','',
            '<!-- CONFIG:ad-core -->','```yaml',yaml.safe_dump(declaration,allow_unicode=True,sort_keys=False,width=120).rstrip(),'```','',
            '默认基础规则payload（无需MITM；扩展覆写替换同一个provider）：','','```yaml',
            yaml.safe_dump(load('rules/ads-basic.yaml'),allow_unicode=True,sort_keys=False).rstrip(),'```','',
            '## 11. 关键输入校验值','',
            '这些哈希用于核对公开源与生成结果，不包含手机私人配置。运行文件及发布提交另看PROGRESS和发布审计。','',
            '| 文件 | SHA256 |','|---|---|']
    sources = ['config/stash.yaml','config/main.yaml','config/core.stoverride',
               'rules/ads-basic.yaml','rules/vendor/ads-expanded.yaml',
               'research/ad-catalog.json','research/sources.lock.json','research/ad-repair-evidence.json',
               'tools/generate_ad_modules.py','tools/build_ad_scripts.py','tools/build_ad_diagnostics.py',
               'tools/build_subscription.py','tools/build_local_bundle.py','tools/build_private_config.py',
               'tools/render_ad_architecture.py','tools/build_ads.py','modules/diagnostics/ads.stoverride']
    sources += [str(p) for p in modules]
    sources += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'scripts/ads').glob('*.js'))]
    sources += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'tools/ad_transforms').glob('*.js'))]
    hashes = {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}
    for p in ['config/stash.yaml','config/core.stoverride','tools/build_ad_scripts.py',*sorted(str(p.relative_to(ROOT)) for p in (ROOT/'scripts/ads').glob('*.js'))]:
        out.append(f'| [{p}](../{p}) | `{hashes[p]}` |')
    out += ['','完整输入哈希和结构计数见 [ad-architecture-audit.json](../research/ad-architecture-audit.json)。','',
            '## 12. 当前全部运行JS原文','',
            '其中11份是按需加载的响应处理，另有probe可选诊断，不参与正常去广告。每份代码独立保留许可；下列正文与稳定脚本文件逐字相同。','']
    scripts = sorted((ROOT/'scripts/ads').glob('*.js'))
    for p in scripts:
        rel=str(p.relative_to(ROOT))
        out += [f'### {p.name}','',f'源文件：[{rel}](../{rel})。','',f'<!-- SOURCE:{rel} -->','```javascript',p.read_text().rstrip(),'```','']
    doc=prefix+'\n'.join(out)
    audit={'revision':VERSION,'baseline':'d8ea21e','before_repair_commit':'936fe457b0362d0dc439d769e9fa7faa29d56b5b',
           'counts':counts,'input_sha256':hashes,'prose_prefix_sha256':hashlib.sha256(prefix.encode()).hexdigest(),
           'documentation':{'path':DOC,'bytes':len(doc.encode()),'sha256':hashlib.sha256(doc.encode()).hexdigest(),
                            'source_scripts_embedded':len(scripts)},
           'native_stash_tested':False,'iphone_effect_tested':False,'real_response_samples':0,
           'official_document_body_downloaded':False,'legacy_rewrite_alias_confirmed':False,
           'publication_evidence':'research/subscription-published.json and research/published-audit.json; this generator does not publish'}
    return {DOC:doc,AUDIT:json.dumps(audit,ensure_ascii=False,indent=2)+'\n'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');args=p.parse_args()
    drift=[]
    for name,body in rendered().items():
        path=ROOT/name
        if path.read_text()!=body:
            drift.append(name)
            if args.write:path.write_text(body)
    print(f'{len(drift)} specification files '+('written' if args.write else 'differ'))
    return 0 if args.write or not drift else 1

if __name__=='__main__':raise SystemExit(main())
